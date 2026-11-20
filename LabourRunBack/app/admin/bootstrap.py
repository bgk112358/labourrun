from __future__ import annotations

import argparse
import getpass

from ..config import load_settings
from ..db import init_db
from ..errors import AppError
from .service import create_admin


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a LabourRun admin account",
    )
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", default=None)
    parser.add_argument("--display-name", default="管理员")
    parser.add_argument(
        "--role",
        default="super_admin",
        choices=["super_admin", "operator"],
    )
    args = parser.parse_args()

    password = args.password or getpass.getpass("Password: ")
    settings = load_settings()
    init_db(settings)

    try:
        admin = create_admin(
            settings,
            args.username,
            password,
            args.display_name,
            args.role,
        )
    except AppError as exc:
        print(f"创建失败：{exc.message}")
        raise SystemExit(1) from exc

    print(
        "创建成功：{}（{}，{}）".format(
            admin["username"],
            admin["role"],
            admin["id"],
        )
    )


if __name__ == "__main__":
    main()
