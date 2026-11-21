from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from ..models import APIModel


ActivityStatus = Literal["upcoming", "ongoing", "ended"]
AdminRole = Literal["super_admin", "operator"]


class AdminRule(APIModel):
    no: str = Field(min_length=1, max_length=8)
    text: str = Field(min_length=1, max_length=500)

    @field_validator("no", "text", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class AdminOut(APIModel):
    id: str
    username: str
    display_name: str
    role: str


class AdminLoginRequest(APIModel):
    username: str = Field(
        min_length=3,
        max_length=32,
        pattern=r"^[A-Za-z0-9_]+$",
    )
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, value):
        return value.strip() if isinstance(value, str) else value


class AdminLoginData(APIModel):
    token: str
    expires_in: int
    admin: AdminOut


class ActivityAdminOut(APIModel):
    id: str
    name: str
    notice_text: str
    rules: list[AdminRule] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None
    status: str
    image_url: str | None = None
    updated_at: str
    updated_by: str | None = None


class ActivityAdminUpdate(APIModel):
    name: str = Field(min_length=2, max_length=50)
    notice_text: str = Field(min_length=1, max_length=200)
    rules: list[AdminRule] = Field(min_length=1, max_length=20)
    start_date: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    end_date: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    status: ActivityStatus
    image_url: str | None = Field(default=None, max_length=500)

    @field_validator("name", "notice_text", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("image_url", mode="before")
    @classmethod
    def normalize_image_url(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class ActivityImageOut(APIModel):
    image_url: str
    width: int
    height: int
    bytes: int


class ChallengeRule(APIModel):
    title: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1, max_length=1000)

    @field_validator("title", "content", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class ChallengeAdminOut(APIModel):
    id: str
    title: str
    start_date: str
    end_date: str | None = None
    target_steps: int
    deposit_coupons: str
    participant_count: int
    rules: list[ChallengeRule] = Field(default_factory=list)
    status: str
    updated_at: str
    updated_by: str | None = None


class ChallengeAdminUpdate(APIModel):
    title: str = Field(min_length=2, max_length=50)
    start_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )
    target_steps: int = Field(ge=1, le=100000)
    deposit_coupons: str = Field(pattern=r"^\d+(\.\d{1,2})?$")
    participant_count: int = Field(ge=0)
    rules: list[ChallengeRule] = Field(min_length=1, max_length=20)
    status: ActivityStatus

    @field_validator("title", mode="before")
    @classmethod
    def strip_title(cls, value):
        return value.strip() if isinstance(value, str) else value


class RegistrationAdminItem(APIModel):
    id: str
    real_name: str
    phone_masked: str
    company: str
    status: str
    created_at: str
    updated_at: str
    cancelled_at: str | None = None


class RegistrationAdminDetail(RegistrationAdminItem):
    phone: str | None = None


class RegistrationAdminPage(APIModel):
    items: list[RegistrationAdminItem] = Field(
        default_factory=list,
        alias="list",
    )
    total: int
    page: int
    page_size: int


class AuditLogItem(APIModel):
    id: str
    admin_id: str | None = None
    admin_username: str
    action: str
    resource_type: str
    resource_id: str | None = None
    ip: str | None = None
    created_at: str


class AuditLogDetail(AuditLogItem):
    before: dict | None = None
    after: dict | None = None
    user_agent: str | None = None


class AuditLogPage(APIModel):
    items: list[AuditLogItem] = Field(
        default_factory=list,
        alias="list",
    )
    total: int
    page: int
    page_size: int


class DashboardActivity(APIModel):
    id: str
    name: str
    status: str
    notice_text: str | None = None
    updated_at: str


class DashboardChallenge(APIModel):
    id: str
    title: str
    status: str
    target_steps: int
    participant_count: int
    updated_at: str


class DashboardData(APIModel):
    activity: DashboardActivity | None = None
    challenge: DashboardChallenge | None = None
    registration_count: int
    today_registration_count: int
    recent_audit_logs: list[AuditLogItem] = Field(default_factory=list)


class RewardAdminOut(APIModel):
    id: str
    activity_id: str
    name: str
    image_url: str | None = None
    coupon_cost: str
    sort_order: int
    active: bool
    updated_at: str


class RewardAdminList(APIModel):
    items: list[RewardAdminOut] = Field(
        default_factory=list,
        alias="list",
    )


class RewardAdminUpdate(APIModel):
    name: str = Field(min_length=1, max_length=50)
    coupon_cost: str = Field(pattern=r"^\d+(\.\d{1,2})?$")
    image_url: str | None = Field(default=None, max_length=500)
    sort_order: int = Field(ge=0, le=9999)
    active: bool

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("image_url", mode="before")
    @classmethod
    def normalize_image_url(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class RewardImageOut(APIModel):
    image_url: str
    width: int
    height: int
    bytes: int


class RewardRedemptionInfo(APIModel):
    id: str
    code: str
    reward_id: str
    reward_name: str
    coupon_cost: str
    activity_name: str
    created_at: str


class RewardRedeemerInfo(APIModel):
    real_name: str
    phone: str | None = None
    phone_masked: str
    company: str


class RewardUserInfo(APIModel):
    id: str
    nickname: str | None = None
    created_at: str


class RewardRegistrationInfo(APIModel):
    id: str
    real_name: str
    phone: str | None = None
    phone_masked: str
    company: str
    status: str
    created_at: str
    updated_at: str
    cancelled_at: str | None = None


class RewardCouponAccount(APIModel):
    balance: str
    total_earned: str
    total_spent: str


class RewardStepSummary(APIModel):
    today_steps: int
    today_exchanged_steps: int
    today_convertible_steps: int
    total_steps: int
    total_exchanged_steps: int
    daily_cap_steps: int
    steps_per_coupon: int


class RewardDailyStep(APIModel):
    stat_date: str
    steps: int
    exchanged_steps: int


class RewardRedemptionHistory(APIModel):
    code: str
    reward_name: str
    coupon_cost: str
    created_at: str


class RewardLedgerItem(APIModel):
    id: str
    type: str
    amount: str
    balance_after: str
    ref_type: str | None = None
    ref_id: str | None = None
    created_at: str


class RewardLookupData(APIModel):
    redemption: RewardRedemptionInfo
    redeemer: RewardRedeemerInfo
    user: RewardUserInfo
    registration: RewardRegistrationInfo | None = None
    coupon_account: RewardCouponAccount
    step_summary: RewardStepSummary
    daily_steps: list[RewardDailyStep] = Field(default_factory=list)
    redemptions: list[RewardRedemptionHistory] = Field(default_factory=list)
    ledger: list[RewardLedgerItem] = Field(default_factory=list)
