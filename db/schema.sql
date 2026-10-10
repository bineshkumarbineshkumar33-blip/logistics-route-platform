-- Used automatically by docker-compose (PostgreSQL + PostGIS).
CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS orders (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    lat        DOUBLE PRECISION NOT NULL,
    lng        DOUBLE PRECISION NOT NULL,
    weight_kg  DOUBLE PRECISION NOT NULL,
    priority   INTEGER NOT NULL DEFAULT 1,
    status     TEXT NOT NULL DEFAULT 'pending',
    -- PostGIS point built from lat/lng, ready for spatial queries
    geom       geography(Point, 4326)
               GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography) STORED
);
CREATE INDEX IF NOT EXISTS orders_geom_idx ON orders USING GIST (geom);

-- Example spatial query: orders within 3 km of the hub
-- SELECT id, name FROM orders
-- WHERE ST_DWithin(geom, ST_MakePoint(78.3772, 17.4435)::geography, 3000);
