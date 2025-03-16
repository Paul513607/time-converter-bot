CREATE TABLE IF NOT EXISTS user_timezone (
    user_id BIGINT PRIMARY KEY,
    timezone VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS message_id_timestamp (
    message_id BIGINT PRIMARY KEY,
    timestamp BIGINT NOT NULL
);