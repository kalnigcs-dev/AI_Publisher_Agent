#!/usr/bin/env bash
set -e

echo "=== Stopping WordPress container (wp-app) ==="
sudo docker stop wp-app 2>/dev/null || true

echo "=== Stopping MariaDB container (wp-db) ==="
sudo docker stop wp-db 2>/dev/null || true

echo ""
echo "=== Success! WordPress and MariaDB containers are stopped. ==="
