ALTER TABLE bookings ADD COLUMN IF NOT EXISTS owner_user_id TEXT;
CREATE INDEX IF NOT EXISTS bookings_owner_history_idx
ON bookings (owner_user_id, created_at DESC, reference DESC)
WHERE owner_user_id IS NOT NULL;
