CREATE TABLE IF NOT EXISTS poop_break_sessions (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    guild_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    started_at DATETIME NOT NULL,
    finished_at DATETIME NULL,
    duration_seconds INT UNSIGNED NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'aberta',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_sessions_guild_user_status (guild_id, user_id, status),
    INDEX idx_sessions_guild_started_at (guild_id, started_at),
    INDEX idx_sessions_guild_finished_at (guild_id, finished_at),
    INDEX idx_sessions_guild_user_finished (guild_id, user_id, finished_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
