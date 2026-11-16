-- Nova AgriSense PostgreSQL + PostGIS initialization script
-- Execute with an administrative role against the target Cloud SQL database.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Verify PostGIS availability
SELECT PostGIS_Full_Version();
