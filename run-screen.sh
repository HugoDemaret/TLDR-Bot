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

echo "Starting Discord Bot..."

# Run the bot using screen
screen -dmS discordBot python3 -m discordBot.py

echo "Discord Bot started."

