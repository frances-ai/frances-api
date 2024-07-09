DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'DefoeQueryConfigs'
        AND column_name = 'level'
    ) THEN
        ALTER TABLE DefoeQueryConfigs ADD COLUMN level VARCHAR(20);
    END IF;
END$$;