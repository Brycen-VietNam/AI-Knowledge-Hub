-- Migration: 010_seed_admin_group_demo_user.sql
-- Feature: admin-spa / S000 — seed data for local dev
-- Task: Create admin group (is_admin=true) + demo user + membership
-- Decision: D01 — admin gate = is_admin flag on user_groups
-- Decision: D08 — user→group via user_group_memberships junction table
-- Requires: migrations 004 (users table), 008 (password_hash), 009 (is_admin + user_group_memberships)

-- ---------------------------------------------------------------------------
-- UP
-- ---------------------------------------------------------------------------

-- 1. Create admin group with is_admin=true
INSERT INTO user_groups (name, is_admin)
VALUES ('admin', TRUE)
ON CONFLICT DO NOTHING;

-- 2. Add existing demo user to admin group via junction table
--    Assumes user with sub='demo' already exists (created by prior seed/migration)
INSERT INTO user_group_memberships (user_id, group_id)
SELECT u.id, g.id
FROM   users       u
JOIN   user_groups g ON g.name = 'admin'
WHERE  u.sub = 'demo'
ON CONFLICT DO NOTHING;

-- ---------------------------------------------------------------------------
-- ROLLBACK
-- ---------------------------------------------------------------------------

-- DELETE FROM user_group_memberships
--   WHERE user_id = (SELECT id FROM users WHERE sub = 'demo')
--     AND group_id = (SELECT id FROM user_groups WHERE name = 'admin');
-- DELETE FROM user_groups WHERE name = 'admin' AND is_admin = TRUE;
