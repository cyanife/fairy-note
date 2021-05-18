-- upgrade --
CREATE TABLE IF NOT EXISTS "chatmsg_6599622" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "userid" VARCHAR(20) NOT NULL,
    "nickname" VARCHAR(100) NOT NULL,
    "time" TIMESTAMPTZ NOT NULL,
    "chatmsg" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "user" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(255) NOT NULL UNIQUE,
    "hashed_password" VARCHAR(255) NOT NULL,
    "is_active" BOOL NOT NULL  DEFAULT True
);
CREATE INDEX IF NOT EXISTS "idx_user_usernam_9987ab" ON "user" ("username");
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" TEXT NOT NULL
);
