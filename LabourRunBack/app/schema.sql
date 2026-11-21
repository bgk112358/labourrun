PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    openid TEXT NOT NULL UNIQUE,
    unionid TEXT,
    avatar_url TEXT,
    nickname TEXT,
    phone TEXT,
    session_key_enc TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    notice_text TEXT,
    rules_json TEXT NOT NULL DEFAULT '[]',
    start_date TEXT,
    end_date TEXT,
    status TEXT NOT NULL DEFAULT 'ongoing'
        CHECK (status IN ('upcoming', 'ongoing', 'ended')),
    image_url TEXT,
    updated_by_admin_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS registrations (
    id TEXT PRIMARY KEY,
    activity_id TEXT NOT NULL REFERENCES activities(id),
    user_id TEXT NOT NULL REFERENCES users(id),
    real_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    company TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'registered'
        CHECK (status IN ('registered', 'cancelled')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    cancelled_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_reg_activity_user
    ON registrations(activity_id, user_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_reg_activity_phone
    ON registrations(activity_id, phone);
CREATE INDEX IF NOT EXISTS ix_reg_user ON registrations(user_id);

CREATE TABLE IF NOT EXISTS daily_steps (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    stat_date TEXT NOT NULL,
    steps INTEGER NOT NULL DEFAULT 0,
    exchanged_steps INTEGER NOT NULL DEFAULT 0,
    source TEXT NOT NULL DEFAULT 'werun',
    synced_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_daily_user_date
    ON daily_steps(user_id, stat_date);

CREATE TABLE IF NOT EXISTS exchange_records (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    stat_date TEXT NOT NULL,
    steps INTEGER NOT NULL,
    coupon_cents INTEGER NOT NULL,
    steps_per_coupon INTEGER NOT NULL,
    request_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'success'
        CHECK (status IN ('success')),
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_exchange_user_request
    ON exchange_records(user_id, request_id);
CREATE INDEX IF NOT EXISTS ix_exchange_user_date
    ON exchange_records(user_id, stat_date);

CREATE TABLE IF NOT EXISTS coupon_accounts (
    user_id TEXT PRIMARY KEY REFERENCES users(id),
    balance_cents INTEGER NOT NULL DEFAULT 0,
    total_earned_cents INTEGER NOT NULL DEFAULT 0,
    total_spent_cents INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS coupon_ledger (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    type TEXT NOT NULL
        CHECK (type IN (
            'exchange', 'reward', 'challenge_deposit',
            'refund', 'adjust'
        )),
    amount_cents INTEGER NOT NULL,
    balance_after_cents INTEGER NOT NULL,
    ref_type TEXT,
    ref_id TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_ledger_user_created
    ON coupon_ledger(user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS rewards (
    id TEXT PRIMARY KEY,
    activity_id TEXT NOT NULL REFERENCES activities(id),
    name TEXT NOT NULL,
    image_url TEXT,
    coupon_cost_cents INTEGER NOT NULL
        CHECK (coupon_cost_cents > 0),
    sort_order INTEGER NOT NULL DEFAULT 0,
    active INTEGER NOT NULL DEFAULT 1
        CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_rewards_activity
    ON rewards(activity_id, sort_order, id);

CREATE TABLE IF NOT EXISTS reward_redemptions (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL REFERENCES users(id),
    registration_id TEXT NOT NULL REFERENCES registrations(id),
    reward_id TEXT NOT NULL REFERENCES rewards(id),
    activity_id TEXT NOT NULL REFERENCES activities(id),
    reward_name TEXT NOT NULL,
    coupon_cost_cents INTEGER NOT NULL,
    real_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    company TEXT NOT NULL,
    request_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'success'
        CHECK (status IN ('success')),
    created_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_reward_user_reward
    ON reward_redemptions(user_id, reward_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_reward_user_request
    ON reward_redemptions(user_id, request_id);
CREATE INDEX IF NOT EXISTS ix_reward_user_created
    ON reward_redemptions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_reward_activity_created
    ON reward_redemptions(activity_id, created_at DESC);

CREATE TABLE IF NOT EXISTS challenges (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    target_steps INTEGER NOT NULL,
    deposit_cents INTEGER NOT NULL DEFAULT 0,
    participant_count INTEGER NOT NULL DEFAULT 0,
    rules_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'upcoming'
        CHECK (status IN ('upcoming', 'ongoing', 'ended')),
    updated_by_admin_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS admin_users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'operator'
        CHECK (role IN ('super_admin', 'operator')),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'disabled')),
    last_login_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS admin_audit_logs (
    id TEXT PRIMARY KEY,
    admin_id TEXT,
    admin_username TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    before_json TEXT,
    after_json TEXT,
    ip TEXT,
    user_agent TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_admin_audit_created
    ON admin_audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_admin_audit_admin
    ON admin_audit_logs(admin_id);
CREATE INDEX IF NOT EXISTS ix_admin_audit_resource
    ON admin_audit_logs(resource_type);
