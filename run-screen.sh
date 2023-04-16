#!/usr/bin/env bash

echo "Starting Discord Bot..."

# Run the bot using screen
screen -dmS discordBot python3 -m discordBot.py

echo "Discord Bot started."

