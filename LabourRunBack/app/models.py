from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

T = TypeVar("T")


class APIModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class ApiResponse(APIModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: T
    request_id: str


class UserOut(APIModel):
    id: str
    nickname: str | None = None
    avatar_url: str | None = None
    phone: str | None = None


class RuleItem(APIModel):
    no: str
    text: str


class ActivityOut(APIModel):
    id: str
    name: str
    notice_text: str | None = None
    rules: list[RuleItem] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None
    status: str
    image_url: str | None = None


class RegistrationOut(APIModel):
    id: str
    activity_id: str
    real_name: str
    phone: str
    company: str
    status: str
    created_at: str
    updated_at: str
    cancelled_at: str | None = None


class CouponAccountOut(APIModel):
    balance: str
    total_earned: str
    total_spent: str


class StepSummaryOut(APIModel):
    today_steps: int
    exchanged_steps: int
    convertible_steps: int
    convertible_coupons: str
    daily_cap_steps: int
    steps_per_coupon: int
    last_synced_at: str | None = None


class ChallengeSummaryOut(APIModel):
    id: str
    title: str
    start_date: str
    end_date: str | None = None
    target_steps: int
    deposit_coupons: str
    participant_count: int
    status: str


class ChallengeRuleOut(APIModel):
    title: str
    content: str


class ChallengeOut(ChallengeSummaryOut):
    rules: list[ChallengeRuleOut] = Field(default_factory=list)


class HomeData(APIModel):
    activity: ActivityOut
    registration: RegistrationOut | None = None


class StepsData(APIModel):
    coupon_account: CouponAccountOut
    step_summary: StepSummaryOut
    challenge: ChallengeSummaryOut | None = None


class LoginData(APIModel):
    token: str
    expires_in: int
    user: UserOut


class SyncData(APIModel):
    coupon_account: CouponAccountOut
    step_summary: StepSummaryOut


class ExchangeResult(APIModel):
    id: str
    steps: int
    coupon_amount: str
    steps_per_coupon: int
    created_at: str


class ExchangeData(APIModel):
    exchange: ExchangeResult
    coupon_account: CouponAccountOut
    step_summary: StepSummaryOut


class LedgerItem(APIModel):
    id: str
    type: str
    amount: str
    balance_after: str
    ref_type: str | None = None
    ref_id: str | None = None
    created_at: str


class LedgerPage(APIModel):
    items: list[LedgerItem] = Field(default_factory=list, alias="list")
    total: int
    page: int
    page_size: int


class LoginRequest(APIModel):
    code: str = Field(min_length=1, max_length=128)

    @field_validator("code", mode="before")
    @classmethod
    def strip_code(cls, value):
        return value.strip() if isinstance(value, str) else value


class RegistrationCreate(APIModel):
    real_name: str = Field(min_length=2, max_length=20)
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    company: str = Field(min_length=2, max_length=50)

    @field_validator("real_name", "phone", "company", mode="before")
    @classmethod
    def strip_strings(cls, value):
        return value.strip() if isinstance(value, str) else value


class RegistrationUpdate(APIModel):
    real_name: str | None = Field(default=None, min_length=2, max_length=20)
    phone: str | None = Field(default=None, pattern=r"^1[3-9]\d{9}$")
    company: str | None = Field(default=None, min_length=2, max_length=50)

    @field_validator("real_name", "phone", "company", mode="before")
    @classmethod
    def strip_strings(cls, value):
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_one_field(self):
        if self.real_name is None and self.phone is None and self.company is None:
            raise ValueError("至少提供一个修改字段")
        return self


class StepSyncRequest(APIModel):
    encrypted_data: str | None = Field(default=None, min_length=1)
    iv: str | None = Field(default=None, min_length=1)
    mock_steps: int | None = Field(default=None, ge=0, le=200000)

    @model_validator(mode="after")
    def validate_payload(self):
        if self.mock_steps is not None:
            if self.encrypted_data is not None or self.iv is not None:
                raise ValueError("mockSteps 不能与 encryptedData/iv 同时提供")
        elif not (self.encrypted_data and self.iv):
            raise ValueError("需要提供 encryptedData + iv，或 mockSteps")
        return self


class ExchangeRequest(APIModel):
    request_id: str = Field(
        min_length=8,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
    )


class MeUpdate(APIModel):
    nickname: str | None = Field(default=None, min_length=1, max_length=32)

    @field_validator("nickname", mode="before")
    @classmethod
    def strip_nickname(cls, value):
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_nickname(self):
        if self.nickname is None:
            raise ValueError("nickname 不能为空")
        return self
