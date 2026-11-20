from __future__ import annotations

import csv
import io
import json
import re
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import Request

from ..config import Settings
from ..db import get_conn, transaction
from ..errors import AppError, ErrorCode
from ..ids import new_id
from ..services.common import (
    get_current_activity,
    get_current_challenge,
)
from ..timeutil import (
    format_cents,
    start_of_today_shanghai_utc_iso,
    utc_now_iso,
)
from .audit import client_ip, write_audit
from .models import (
    ActivityAdminUpdate,
    ChallengeAdminUpdate,
)
from .security import (
    check_login_allowed,
    clear_login_failures,
    create_admin_token,
    hash_password,
    record_login_failure,
    validate_password_policy,
    verify_password,
)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,32}$")
VALID_STATUS = {"upcoming", "ongoing", "ended"}


def _json_list(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return value if isinstance(value, list) else []


def _json_dict(raw: str | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def admin_public(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "role": row["role"],
    }


def _audit_item(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "admin_id": row["admin_id"],
        "admin_username": row["admin_username"],
        "action": row["action"],
        "resource_type": row["resource_type"],
        "resource_id": row["resource_id"],
        "ip": row["ip"],
        "created_at": row["created_at"],
    }


def _admin_username(
    conn: sqlite3.Connection,
    admin_id: str | None,
) -> str | None:
    if not admin_id:
        return None
    row = conn.execute(
        "SELECT username FROM admin_users WHERE id = ?",
        (admin_id,),
    ).fetchone()
    return row["username"] if row is not None else None


def _activity_admin(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "notice_text": row["notice_text"] or "",
        "rules": _json_list(row["rules_json"]),
        "start_date": row["start_date"],
        "end_date": row["end_date"],
        "status": row["status"],
        "updated_at": row["updated_at"],
        "updated_by": _admin_username(conn, row["updated_by_admin_id"]),
    }


def _challenge_admin(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "start_date": row["start_date"],
        "end_date": row["end_date"],
        "target_steps": row["target_steps"],
        "deposit_coupons": format_cents(row["deposit_cents"]),
        "participant_count": row["participant_count"],
        "rules": _json_list(row["rules_json"]),
        "status": row["status"],
        "updated_at": row["updated_at"],
        "updated_by": _admin_username(conn, row["updated_by_admin_id"]),
    }


def _activity_snapshot(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": data["id"],
        "name": data["name"],
        "noticeText": data["notice_text"],
        "rules": data["rules"],
        "startDate": data["start_date"],
        "endDate": data["end_date"],
        "status": data["status"],
        "updatedAt": data["updated_at"],
        "updatedBy": data["updated_by"],
    }


def _challenge_snapshot(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": data["id"],
        "title": data["title"],
        "startDate": data["start_date"],
        "endDate": data["end_date"],
        "targetSteps": data["target_steps"],
        "depositCoupons": data["deposit_coupons"],
        "participantCount": data["participant_count"],
        "rules": data["rules"],
        "status": data["status"],
        "updatedAt": data["updated_at"],
        "updatedBy": data["updated_by"],
    }


def _dashboard_activity(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "status": row["status"],
        "notice_text": row["notice_text"],
        "updated_at": row["updated_at"],
    }


def _dashboard_challenge(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "status": row["status"],
        "target_steps": row["target_steps"],
        "participant_count": row["participant_count"],
        "updated_at": row["updated_at"],
    }


def _parse_date(value: str | None, label: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            400,
            f"{label}格式不正确",
        ) from exc


def _validate_date_range(
    start_date: str | None,
    end_date: str | None,
) -> None:
    start = _parse_date(start_date, "开始日期")
    end = _parse_date(end_date, "结束日期")
    if start is not None and end is not None and start > end:
        raise AppError(
            ErrorCode.ADMIN_CONFIG_INVALID,
            422,
            "开始日期不能晚于结束日期",
        )


def _validate_rule_numbers(rules) -> None:
    seen: set[str] = set()
    for rule in rules:
        if rule.no in seen:
            raise AppError(
                ErrorCode.ADMIN_CONFIG_INVALID,
                422,
                f"规则编号 {rule.no} 重复",
            )
        seen.add(rule.no)


def _parse_coupons_to_cents(value: str) -> int:
    try:
        amount = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            400,
            "保证金格式不正确",
        ) from exc

    if amount < 0:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            400,
            "保证金不能为负数",
        )
    if amount > Decimal("1000000"):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            400,
            "保证金超出范围",
        )
    if amount.as_tuple().exponent < -2:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            400,
            "保证金最多保留 2 位小数",
        )
    return int(amount * 100)


def _mask_phone(phone: str) -> str:
    if len(phone) >= 7:
        return f"{phone[:3]}****{phone[-4:]}"
    return "****"


def _registration_where(
    keyword: str | None,
    status: str | None,
) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if keyword:
        like = f"%{keyword.strip()}%"
        clauses.append(
            "(real_name LIKE ? OR phone LIKE ? OR company LIKE ?)"
        )
        params.extend([like, like, like])

    if status:
        if status not in {"registered", "cancelled"}:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                400,
                "status 只能是 registered 或 cancelled",
            )
        clauses.append("status = ?")
        params.append(status)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


def admin_login(
    settings: Settings,
    request: Request,
    username: str,
    password: str,
) -> dict[str, Any]:
    key = f"{username}:{client_ip(request) or '-'}"
    check_login_allowed(key)
    failure: AppError | None = None
    admin_data: dict[str, Any] | None = None

    with transaction(settings) as conn:
        row = conn.execute(
            "SELECT * FROM admin_users WHERE username = ?",
            (username,),
        ).fetchone()

        if row is None or not verify_password(password, row["password_hash"]):
            write_audit(
                conn,
                request,
                None,
                username,
                "login_failed",
                "auth",
            )
            failure = AppError(
                ErrorCode.ADMIN_LOGIN_FAILED,
                401,
                "用户名或密码错误",
            )
        elif row["status"] != "active":
            write_audit(
                conn,
                request,
                row["id"],
                row["username"],
                "login_failed",
                "auth",
                row["id"],
            )
            failure = AppError(
                ErrorCode.ADMIN_DISABLED,
                403,
                "管理员账号已禁用",
            )
        else:
            now = utc_now_iso()
            conn.execute(
                """
                UPDATE admin_users
                SET last_login_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (now, now, row["id"]),
            )
            admin_data = admin_public(row)
            write_audit(
                conn,
                request,
                row["id"],
                row["username"],
                "login",
                "auth",
                row["id"],
                after=admin_data,
            )

    if failure is not None:
        record_login_failure(key)
        raise failure

    clear_login_failures(key)
    assert admin_data is not None
    return {
        "token": create_admin_token(settings, admin_data),
        "expires_in": settings.admin_jwt_ttl_seconds,
        "admin": admin_data,
    }


def get_admin(settings: Settings, admin_id: str) -> dict[str, Any]:
    with get_conn(settings) as conn:
        row = conn.execute(
            "SELECT * FROM admin_users WHERE id = ?",
            (admin_id,),
        ).fetchone()
    if row is None:
        raise AppError(
            ErrorCode.ADMIN_NOT_FOUND,
            404,
            "管理员不存在",
        )
    return admin_public(row)


def get_dashboard(settings: Settings) -> dict[str, Any]:
    with get_conn(settings) as conn:
        activity = get_current_activity(conn)
        challenge = get_current_challenge(conn)
        registration_count = conn.execute(
            "SELECT COUNT(*) AS n FROM registrations"
        ).fetchone()["n"]
        today_start = start_of_today_shanghai_utc_iso()
        today_count = conn.execute(
            """
            SELECT COUNT(*) AS n
            FROM registrations
            WHERE created_at >= ?
            """,
            (today_start,),
        ).fetchone()["n"]
        logs = conn.execute(
            """
            SELECT *
            FROM admin_audit_logs
            ORDER BY created_at DESC, id DESC
            LIMIT 5
            """
        ).fetchall()

    return {
        "activity": _dashboard_activity(activity),
        "challenge": _dashboard_challenge(challenge),
        "registration_count": registration_count,
        "today_registration_count": today_count,
        "recent_audit_logs": [_audit_item(row) for row in logs],
    }


def get_activity(settings: Settings) -> dict[str, Any]:
    with get_conn(settings) as conn:
        row = get_current_activity(conn)
        if row is None:
            raise AppError(
                ErrorCode.ADMIN_ACTIVITY_NOT_FOUND,
                404,
                "活动不存在",
            )
        return _activity_admin(conn, row)


def update_activity(
    settings: Settings,
    request: Request,
    admin: sqlite3.Row,
    body: ActivityAdminUpdate,
) -> dict[str, Any]:
    _validate_date_range(body.start_date, body.end_date)
    _validate_rule_numbers(body.rules)

    rules_json = json.dumps(
        [{"no": rule.no, "text": rule.text} for rule in body.rules],
        ensure_ascii=False,
    )
    now = utc_now_iso()

    with transaction(settings) as conn:
        before_row = get_current_activity(conn)
        if before_row is None:
            raise AppError(
                ErrorCode.ADMIN_ACTIVITY_NOT_FOUND,
                404,
                "活动不存在",
            )
        before = _activity_admin(conn, before_row)

        conn.execute(
            """
            UPDATE activities
            SET name = ?, notice_text = ?, rules_json = ?,
                start_date = ?, end_date = ?, status = ?,
                updated_by_admin_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                body.name,
                body.notice_text,
                rules_json,
                body.start_date,
                body.end_date,
                body.status,
                admin["id"],
                now,
                before_row["id"],
            ),
        )

        after_row = conn.execute(
            "SELECT * FROM activities WHERE id = ?",
            (before_row["id"],),
        ).fetchone()
        after = _activity_admin(conn, after_row)
        write_audit(
            conn,
            request,
            admin["id"],
            admin["username"],
            "update_activity",
            "activity",
            after["id"],
            _activity_snapshot(before),
            _activity_snapshot(after),
        )

    return after


def get_challenge(settings: Settings) -> dict[str, Any]:
    with get_conn(settings) as conn:
        row = get_current_challenge(conn)
        if row is None:
            raise AppError(
                ErrorCode.ADMIN_CHALLENGE_NOT_FOUND,
                404,
                "挑战不存在",
            )
        return _challenge_admin(conn, row)


def update_challenge(
    settings: Settings,
    request: Request,
    admin: sqlite3.Row,
    body: ChallengeAdminUpdate,
) -> dict[str, Any]:
    _validate_date_range(body.start_date, body.end_date)
    deposit_cents = _parse_coupons_to_cents(body.deposit_coupons)
    rules_json = json.dumps(
        [
            {"title": rule.title, "content": rule.content}
            for rule in body.rules
        ],
        ensure_ascii=False,
    )
    now = utc_now_iso()

    with transaction(settings) as conn:
        before_row = get_current_challenge(conn)
        if before_row is None:
            raise AppError(
                ErrorCode.ADMIN_CHALLENGE_NOT_FOUND,
                404,
                "挑战不存在",
            )
        before = _challenge_admin(conn, before_row)

        conn.execute(
            """
            UPDATE challenges
            SET title = ?, start_date = ?, end_date = ?,
                target_steps = ?, deposit_cents = ?,
                participant_count = ?, rules_json = ?, status = ?,
                updated_by_admin_id = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                body.title,
                body.start_date,
                body.end_date,
                body.target_steps,
                deposit_cents,
                body.participant_count,
                rules_json,
                body.status,
                admin["id"],
                now,
                before_row["id"],
            ),
        )

        after_row = conn.execute(
            "SELECT * FROM challenges WHERE id = ?",
            (before_row["id"],),
        ).fetchone()
        after = _challenge_admin(conn, after_row)
        write_audit(
            conn,
            request,
            admin["id"],
            admin["username"],
            "update_challenge",
            "challenge",
            after["id"],
            _challenge_snapshot(before),
            _challenge_snapshot(after),
        )

    return after


def list_registrations(
    settings: Settings,
    page: int,
    page_size: int,
    keyword: str | None,
    status: str | None,
) -> dict[str, Any]:
    where, params = _registration_where(keyword, status)
    offset = (page - 1) * page_size

    with get_conn(settings) as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS n FROM registrations {where}",
            params,
        ).fetchone()["n"]
        rows = conn.execute(
            f"""
            SELECT *
            FROM registrations
            {where}
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        ).fetchall()

    items = [
        {
            "id": row["id"],
            "real_name": row["real_name"],
            "phone_masked": _mask_phone(row["phone"]),
            "company": row["company"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "cancelled_at": row["cancelled_at"],
        }
        for row in rows
    ]
    return {
        "list": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_registration(
    settings: Settings,
    admin: sqlite3.Row,
    registration_id: str,
) -> dict[str, Any]:
    with get_conn(settings) as conn:
        row = conn.execute(
            "SELECT * FROM registrations WHERE id = ?",
            (registration_id,),
        ).fetchone()

    if row is None:
        raise AppError(
            ErrorCode.ADMIN_REGISTRATION_NOT_FOUND,
            404,
            "报名记录不存在",
        )

    return {
        "id": row["id"],
        "real_name": row["real_name"],
        "phone": row["phone"] if admin["role"] == "super_admin" else None,
        "phone_masked": _mask_phone(row["phone"]),
        "company": row["company"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "cancelled_at": row["cancelled_at"],
    }


def export_registrations(
    settings: Settings,
    admin: sqlite3.Row,
    keyword: str | None,
    status: str | None,
) -> str:
    if admin["role"] != "super_admin":
        raise AppError(
            ErrorCode.ADMIN_FORBIDDEN,
            403,
            "只有超级管理员可以导出报名数据",
        )

    where, params = _registration_where(keyword, status)
    with get_conn(settings) as conn:
        rows = conn.execute(
            f"""
            SELECT *
            FROM registrations
            {where}
            ORDER BY created_at DESC, id DESC
            """,
            params,
        ).fetchall()

    output = io.StringIO()
    output.write(chr(0xFEFF))
    writer = csv.writer(output)
    writer.writerow(
        [
            "姓名",
            "手机号",
            "工作单位",
            "状态",
            "报名时间",
            "更新时间",
            "取消时间",
        ]
    )
    for row in rows:
        status_label = "已报名" if row["status"] == "registered" else "已取消"
        writer.writerow(
            [
                row["real_name"],
                row["phone"],
                row["company"],
                status_label,
                row["created_at"],
                row["updated_at"],
                row["cancelled_at"] or "",
            ]
        )
    return output.getvalue()


def list_audit_logs(
    settings: Settings,
    page: int,
    page_size: int,
    admin_id: str | None,
    resource_type: str | None,
    from_date: str | None,
    to_date: str | None,
) -> dict[str, Any]:
    clauses: list[str] = []
    params: list[Any] = []

    if admin_id:
        clauses.append("admin_id = ?")
        params.append(admin_id)
    if resource_type:
        clauses.append("resource_type = ?")
        params.append(resource_type)

    if from_date:
        _parse_date(from_date, "开始日期")
        clauses.append("created_at >= ?")
        params.append(from_date)

    if to_date:
        _parse_date(to_date, "结束日期")
        clauses.append("created_at <= ?")
        params.append(f"{to_date}T23:59:59.999Z")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    offset = (page - 1) * page_size

    with get_conn(settings) as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS n FROM admin_audit_logs {where}",
            params,
        ).fetchone()["n"]
        rows = conn.execute(
            f"""
            SELECT *
            FROM admin_audit_logs
            {where}
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        ).fetchall()

    return {
        "list": [_audit_item(row) for row in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


def get_audit_log(settings: Settings, log_id: str) -> dict[str, Any]:
    with get_conn(settings) as conn:
        row = conn.execute(
            "SELECT * FROM admin_audit_logs WHERE id = ?",
            (log_id,),
        ).fetchone()

    if row is None:
        raise AppError(
            ErrorCode.NOT_FOUND,
            404,
            "审计日志不存在",
        )

    return {
        **_audit_item(row),
        "before": _json_dict(row["before_json"]),
        "after": _json_dict(row["after_json"]),
        "user_agent": row["user_agent"],
    }


def create_admin(
    settings: Settings,
    username: str,
    password: str,
    display_name: str,
    role: str = "operator",
) -> dict[str, Any]:
    username = username.strip()
    display_name = display_name.strip()

    if not USERNAME_RE.match(username):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            400,
            "用户名需为 3–32 位字母、数字或下划线",
        )
    if not display_name or len(display_name) > 50:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            400,
            "显示名需为 1–50 个字符",
        )
    if role not in {"super_admin", "operator"}:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            400,
            "角色只能是 super_admin 或 operator",
        )
    validate_password_policy(password)

    now = utc_now_iso()
    with transaction(settings) as conn:
        existing = conn.execute(
            "SELECT id FROM admin_users WHERE username = ?",
            (username,),
        ).fetchone()
        if existing is not None:
            raise AppError(
                ErrorCode.ADMIN_USERNAME_EXISTS,
                409,
                "用户名已存在",
            )

        admin_id = new_id("adm")
        conn.execute(
            """
            INSERT INTO admin_users
                (id, username, password_hash, display_name, role,
                 status, last_login_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'active', NULL, ?, ?)
            """,
            (
                admin_id,
                username,
                hash_password(password),
                display_name,
                role,
                now,
                now,
            ),
        )
        row = conn.execute(
            "SELECT * FROM admin_users WHERE id = ?",
            (admin_id,),
        ).fetchone()

    return admin_public(row)
