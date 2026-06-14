CREATE TABLE contexts (
    context_id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE versions (
    version_number INTEGER,
    context_id INTEGER,
    content_hash TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(version_number, context_id)
);

CREATE TABLE locations (
    location TEXT PRIMARY KEY,
    context_id INTEGER,
    provider TEXT,
    status INTEGER DEFAULT 1
);