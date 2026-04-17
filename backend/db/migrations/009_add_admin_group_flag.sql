-- Spec: docs/admin-spa/spec/admin-spa.spec.md#S000
-- Task: T001 — is_admin flag on user_groups + user_group_memberships junction table
-- Rule: A006 — numbered migration file; rollback section at bottom
-- AC1: ALTER TABLE user_groups ADD COLUMN is_admin
-- AC2/AC3 prereq: user_group_memberships needed for is_admin computation in verify_token

ALTER TABLE user_groups ADD COLUMN is_admin BOOL NOT NULL DEFAULT FALSE;

CREATE TABLE user_group_memberships (
    user_id  UUID    NOT NULL REFERENCES users(id)        ON DELETE CASCADE,
    group_id INTEGER NOT NULL REFERENCES user_groups(id)  ON DELETE CASCADE,
    PRIMARY KEY (user_id, group_id)
);

-- Rollback:
-- DROP TABLE user_group_memberships;
-- ALTER TABLE user_groups DROP COLUMN is_admin;
