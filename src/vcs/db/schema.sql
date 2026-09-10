CREATE TABLE IF NOT EXISTS contexts (
    context_id TEXT PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS versions (
    version_number INTEGER,
    context_id INTEGER,
    content_hash TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(version_number, context_id)
);

-- device_id (spec 041) scopes st_ino/st_dev to the device that issued
-- them - a filesystem inode is only meaningful on the filesystem that
-- produced it, and two devices can and will reuse the same one.
CREATE TABLE IF NOT EXISTS locations (
    st_ino TEXT,
    st_dev TEXT,
    device_id TEXT NOT NULL,
    context_id INTEGER,
    location TEXT,
    provider TEXT,
    status INTEGER DEFAULT 1,
    PRIMARY KEY(device_id, st_ino, st_dev)
);

CREATE TABLE IF NOT EXISTS pending_actor_hints (
    location TEXT PRIMARY KEY,
    actor TEXT NOT NULL,
    expires_at REAL NOT NULL
);