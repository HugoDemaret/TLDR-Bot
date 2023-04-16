#!/usr/bin/env bash
cat << 'EOF'
  _____ _           ____  ____
 |_   _| |      _  |  _ \|  _ \
   | | | |     (_) | | | | |_) |
   | | | |___   _  | |_| |  _ <
   |_| |_____| ( ) |____/|_| \_\
               |/
  Too  Long    ;   Didn't Read
EOF

# Running with Docker (docker-compose)

echo "Starting Discord Bot..."

docker-compose up -d

echo "Discord Bot started."

