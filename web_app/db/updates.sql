DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM information_schema.columns
        WHERE table_name = 'DefoeQueryConfigs'
        AND column_name = 'sourceProvider'
    ) THEN
        ALTER TABLE DefoeQueryConfigs ADD COLUMN sourceProvider VARCHAR(20) NOT NULL DEFAULT 'NLS';
    END IF;
END$$;