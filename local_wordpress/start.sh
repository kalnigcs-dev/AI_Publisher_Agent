#!/usr/bin/env bash
set -e

echo "=== Creating Docker network ==="
sudo docker network create wp-net 2>/dev/null || true

echo "=== Starting MariaDB container (wp-db) ==="
sudo docker run -d \
  --name wp-db \
  --network wp-net \
  --restart always \
  -e MYSQL_ROOT_PASSWORD=secretroot \
  -e MYSQL_DATABASE=wordpress \
  -e MYSQL_USER=wordpress \
  -e MYSQL_PASSWORD=secretpass \
  mariadb:10.6 2>/dev/null || sudo docker start wp-db

echo "=== Starting WordPress container (wp-app) on port 8080 ==="
sudo docker run -d \
  --name wp-app \
  --network wp-net \
  --restart always \
  -p 8080:80 \
  -e WORDPRESS_DB_HOST=wp-db \
  -e WORDPRESS_DB_USER=wordpress \
  -e WORDPRESS_DB_PASSWORD=secretpass \
  -e WORDPRESS_DB_NAME=wordpress \
  wordpress:latest 2>/dev/null || sudo docker start wp-app

echo ""
echo "=== Success! WordPress is running at: http://localhost:8080 ==="
