-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Providers
CREATE TABLE IF NOT EXISTS providers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1,
    base_url TEXT NOT NULL DEFAULT '',
    endpoints TEXT NOT NULL DEFAULT '{}',
    api_version TEXT NOT NULL DEFAULT '',
    auth_type TEXT NOT NULL DEFAULT 'api_key',
    custom_headers TEXT NOT NULL DEFAULT '{}',
    timeout_global INTEGER NOT NULL DEFAULT 30,
    timeout_per_modality TEXT NOT NULL DEFAULT '{}',
    retry_count INTEGER NOT NULL DEFAULT 3,
    retry_delay REAL NOT NULL DEFAULT 1.0,
    retry_backoff REAL NOT NULL DEFAULT 2.0,
    proxy TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    extra_fields TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Credentials (sensitive fields stored encrypted)
CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    validity TEXT NOT NULL DEFAULT 'untested',
    api_key TEXT NOT NULL DEFAULT '',
    bearer_token TEXT NOT NULL DEFAULT '',
    oauth_access_token TEXT NOT NULL DEFAULT '',
    oauth_refresh_token TEXT NOT NULL DEFAULT '',
    oauth_client_id TEXT NOT NULL DEFAULT '',
    oauth_client_secret TEXT NOT NULL DEFAULT '',
    oauth_scopes TEXT NOT NULL DEFAULT '',
    oauth_auth_url TEXT NOT NULL DEFAULT '',
    oauth_token_endpoint TEXT NOT NULL DEFAULT '',
    oauth_expires_at TEXT,
    org_id TEXT NOT NULL DEFAULT '',
    project_id TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Models
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
    technical_name TEXT NOT NULL,
    display_name TEXT NOT NULL DEFAULT '',
    type TEXT NOT NULL DEFAULT 'text',
    active INTEGER NOT NULL DEFAULT 1,
    favorite INTEGER NOT NULL DEFAULT 0,
    rating INTEGER,
    context_max INTEGER,
    cost_input REAL,
    cost_output REAL,
    currency TEXT NOT NULL DEFAULT 'USD',
    rpm_limit INTEGER,
    tpm_limit INTEGER,
    tags TEXT NOT NULL DEFAULT '[]',
    notes TEXT NOT NULL DEFAULT '',
    extra TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Model capabilities
CREATE TABLE IF NOT EXISTS model_capabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    capability TEXT NOT NULL,
    UNIQUE(model_id, capability)
);

-- Presets
CREATE TABLE IF NOT EXISTS presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    modality TEXT NOT NULL DEFAULT 'text',
    model_id INTEGER REFERENCES models(id) ON DELETE SET NULL,
    params TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Test runs
CREATE TABLE IF NOT EXISTS test_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider_id INTEGER REFERENCES providers(id) ON DELETE SET NULL,
    credential_id INTEGER REFERENCES credentials(id) ON DELETE SET NULL,
    model_id INTEGER REFERENCES models(id) ON DELETE SET NULL,
    modality TEXT NOT NULL DEFAULT 'text',
    params TEXT NOT NULL DEFAULT '{}',
    request_payload TEXT NOT NULL DEFAULT '{}',
    response_raw TEXT NOT NULL DEFAULT '',
    response_files TEXT NOT NULL DEFAULT '[]',
    latency_ms INTEGER,
    cost_estimated REAL,
    currency TEXT NOT NULL DEFAULT 'USD',
    status TEXT NOT NULL DEFAULT 'pending',
    error_message TEXT NOT NULL DEFAULT '',
    rating INTEGER,
    rating_notes TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Async tasks (for video generation polling)
CREATE TABLE IF NOT EXISTS async_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_run_id INTEGER REFERENCES test_runs(id) ON DELETE CASCADE,
    provider_task_id TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    poll_interval_s INTEGER NOT NULL DEFAULT 10,
    timeout_s INTEGER NOT NULL DEFAULT 600,
    last_polled_at TEXT,
    result TEXT NOT NULL DEFAULT '{}',
    error TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Prompt templates
CREATE TABLE IF NOT EXISTS prompt_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    content TEXT NOT NULL DEFAULT '',
    modality TEXT NOT NULL DEFAULT 'text',
    category TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Record migration version
INSERT OR IGNORE INTO schema_version (version) VALUES (1);
