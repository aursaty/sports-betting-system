#!/bin/bash
set -e

echo "============================================"
echo "Initializing PostgreSQL Master"
echo "============================================"
echo "Database: ${POSTGRES_DB}"
echo "Master User: ${POSTGRES_USER}"
echo "Replica User: ${REPLICA_DATABASE_USER}"
echo "Reader Role: ${DATABASE_READER_ROLE_NAME}"
echo "============================================"

if [ -z "$REPLICA_DATABASE_USER" ] || [ -z "$REPLICA_DATABASE_PASSWORD" ]; then
    echo "ERROR: REPLICA_DATABASE_USER and REPLICA_DATABASE_PASSWORD must be set"
    exit 1
fi

if [ -z "$DATABASE_READER_ROLE_NAME" ] || [ -z "$DATABASE_READER_ROLE_PASSWORD" ]; then
    echo "WARNING: DATABASE_READER_ROLE_NAME and DATABASE_READER_ROLE_PASSWORD not set, skipping reader role creation"
    SKIP_READER=true
fi

echo "Creating replication user..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${REPLICA_DATABASE_USER}') THEN
            CREATE ROLE "${REPLICA_DATABASE_USER}" WITH REPLICATION LOGIN ENCRYPTED PASSWORD '${REPLICA_DATABASE_PASSWORD}';
            RAISE NOTICE 'Replication user created: ${REPLICA_DATABASE_USER}';
        ELSE
            RAISE NOTICE 'Replication user already exists: ${REPLICA_DATABASE_USER}';
        END IF;
    END
    \$\$;
EOSQL

echo "Granting database privileges to replication user..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    GRANT CONNECT ON DATABASE "${POSTGRES_DB}" TO "${REPLICA_DATABASE_USER}";
    GRANT USAGE ON SCHEMA public TO "${REPLICA_DATABASE_USER}";
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO "${REPLICA_DATABASE_USER}";
    GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO "${REPLICA_DATABASE_USER}";
    
    -- Grant privileges on future tables
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO "${REPLICA_DATABASE_USER}";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO "${REPLICA_DATABASE_USER}";
EOSQL

if [ "$SKIP_READER" != "true" ]; then
    echo "Creating reader role..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        DO \$\$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${DATABASE_READER_ROLE_NAME}') THEN
                CREATE ROLE "${DATABASE_READER_ROLE_NAME}" WITH LOGIN ENCRYPTED PASSWORD '${DATABASE_READER_ROLE_PASSWORD}';
                RAISE NOTICE 'Reader role created: ${DATABASE_READER_ROLE_NAME}';
            ELSE
                RAISE NOTICE 'Reader role already exists: ${DATABASE_READER_ROLE_NAME}';
            END IF;
        END
        \$\$;
EOSQL

    echo "Granting database privileges to reader role..."
    psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
        GRANT CONNECT ON DATABASE "${POSTGRES_DB}" TO "${DATABASE_READER_ROLE_NAME}";
        GRANT USAGE ON SCHEMA public TO "${DATABASE_READER_ROLE_NAME}";
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO "${DATABASE_READER_ROLE_NAME}";
        GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO "${DATABASE_READER_ROLE_NAME}";
        
        -- Grant privileges on future tables
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO "${DATABASE_READER_ROLE_NAME}";
        ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO "${DATABASE_READER_ROLE_NAME}";
EOSQL
fi

echo "Creating replication slots..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = 'replication_slot_1') THEN
            PERFORM pg_create_physical_replication_slot('replication_slot_1');
            RAISE NOTICE 'Created replication_slot_1';
        ELSE
            RAISE NOTICE 'replication_slot_1 already exists';
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = 'replication_slot_2') THEN
            PERFORM pg_create_physical_replication_slot('replication_slot_2');
            RAISE NOTICE 'Created replication_slot_2';
        ELSE
            RAISE NOTICE 'replication_slot_2 already exists';
        END IF;
        
        IF NOT EXISTS (SELECT 1 FROM pg_replication_slots WHERE slot_name = 'replication_slot_3') THEN
            PERFORM pg_create_physical_replication_slot('replication_slot_3');
            RAISE NOTICE 'Created replication_slot_3';
        ELSE
            RAISE NOTICE 'replication_slot_3 already exists';
        END IF;
    END
    \$\$;
EOSQL

echo "Configuring pg_hba.conf for replication..."
sed -i '/host replication/d' "$PGDATA/pg_hba.conf"

cat >> "$PGDATA/pg_hba.conf" <<EOF

# Replication connections
host    replication     ${REPLICA_DATABASE_USER}     0.0.0.0/0               scram-sha-256
host    replication     all                          0.0.0.0/0               scram-sha-256

# Database connections for all users
host    all             all                          0.0.0.0/0               scram-sha-256
EOF

echo "pg_hba.conf updated successfully"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "SELECT pg_reload_conf();"

echo "============================================"
echo "PostgreSQL Master Initialization Complete"
echo "============================================"
echo "Available users:"
echo "  - Master user: ${POSTGRES_USER}"
echo "  - Replication user: ${REPLICA_DATABASE_USER}"
if [ "$SKIP_READER" != "true" ]; then
    echo "  - Reader role: ${DATABASE_READER_ROLE_NAME}"
fi
echo "============================================"