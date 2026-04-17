-- M7-T59: Task 1.4 Audit Fix
-- Add must_change_password column to users table
-- Default: false, existing users are not affected

-- Add column if not exists (idempotent)
ALTER TABLE users
ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE NOT NULL;

-- Default admin must change password on first login
-- Only applies if the admin user already exists
UPDATE users
SET must_change_password = TRUE
WHERE username = 'admin' AND must_change_password = FALSE;