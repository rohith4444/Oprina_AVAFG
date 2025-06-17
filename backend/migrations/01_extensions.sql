-- =============================================================================
-- ENABLE REQUIRED EXTENSIONS
-- =============================================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Success message
DO $$
BEGIN
    RAISE NOTICE '✅ Extensions enabled successfully!';
    RAISE NOTICE '🔧 UUID generation available';
END $$;