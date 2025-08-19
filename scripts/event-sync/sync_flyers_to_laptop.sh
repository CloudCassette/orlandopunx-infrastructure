#!/bin/bash
#
📁 Sync Flyers to Laptop
========================
Copies new flyer images to your laptop via SCP/rsync
#

# Configuration
LAPTOP_USER="your_username"  # Change this to your laptop username
LAPTOP_IP="192.168.1.100"   # Change this to your laptop IP
LAPTOP_PATH="~/Downloads/orlando-flyers/"

# Source directory
FLYER_DIR="/home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync/flyers"

echo "🖼️  Syncing flyers to laptop..."
echo "📁 From: $FLYER_DIR"
echo "💻 To: $LAPTOP_USER@$LAPTOP_IP:$LAPTOP_PATH"

# Create directory on laptop if it doesn't exist
ssh "$LAPTOP_USER@$LAPTOP_IP" "mkdir -p $LAPTOP_PATH"

# Sync files (only copy newer files)
rsync -av --progress "$FLYER_DIR/" "$LAPTOP_USER@$LAPTOP_IP:$LAPTOP_PATH"

echo "✅ Sync complete!"
echo "📱 Check your laptop's ~/Downloads/orlando-flyers/ folder"
