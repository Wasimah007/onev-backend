#!/bin/bash

# Database Migration Script
# Usage: ./migrate.sh [environment]
# Environment defaults to 'development' if not specified

set -e

ENVIRONMENT=${1:-development}

# Load environment variables based on environment
if [ "$ENVIRONMENT" = "production" ]; then
    source .env.production 2>/dev/null || echo "Warning: .env.production not found"
elif [ "$ENVIRONMENT" = "test" ]; then
    source .env.test 2>/dev/null || echo "Warning: .env.test not found"
else
    source .env 2>/dev/null || echo "Warning: .env not found"
fi

# Set default values if environment variables are not set
MYSQL_HOST=${MYSQL_HOST:-localhost}
MYSQL_PORT=${MYSQL_PORT:-3306}
MYSQL_USER=${MYSQL_USER:-root}
MYSQL_PASSWORD=${MYSQL_PASSWORD:-password}
MYSQL_DATABASE=${MYSQL_DATABASE:-timesheet_db}

echo "Running database migration for environment: $ENVIRONMENT"
echo "Host: $MYSQL_HOST:$MYSQL_PORT"
echo "Database: $MYSQL_DATABASE"
echo "User: $MYSQL_USER"

# Check if MySQL is accessible
if ! mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "SELECT 1;" > /dev/null 2>&1; then
    echo "Error: Cannot connect to MySQL server"
    echo "Please check your database connection settings"
    exit 1
fi

# Run the schema migration (database creation is handled in schema.sql)
echo "Applying schema changes..."
mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" < schema.sql

echo "Migration completed successfully!"
echo ""
echo "Default admin user created:"
echo "  Email: admin@example.com"
echo "  Username: admin"
echo "  Password: admin123"
echo ""
echo "Please change the admin password after first login!"