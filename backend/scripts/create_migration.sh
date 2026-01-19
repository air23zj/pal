#!/bin/bash
# Create a new Alembic migration

set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/create_migration.sh \"migration message\""
    exit 1
fi

cd "$(dirname "$0")/.."

echo "Creating migration: $1"
alembic revision --autogenerate -m "$1"

echo ""
echo "✅ Migration created!"
echo ""
echo "To apply the migration:"
echo "  alembic upgrade head"
echo ""
echo "To see migration history:"
echo "  alembic history"
