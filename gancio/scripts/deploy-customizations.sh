#!/bin/bash

# Deploy Gancio Customizations Script
# This script applies the custom CSS and configuration to a Gancio installation

set -e  # Exit on any error

echo "=== Gancio Customizations Deployment ==="
echo "Starting deployment at: $(date)"

# Check if running as root/sudo
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root or with sudo" 
   exit 1
fi

# Backup current files
echo "Creating backups..."
BACKUP_DIR="/tmp/gancio-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"

if [ -f "/usr/lib/node_modules/gancio/assets/style.css" ]; then
    cp /usr/lib/node_modules/gancio/assets/style.css "$BACKUP_DIR/style.css.backup"
    echo "Backed up current style.css to $BACKUP_DIR"
fi

# Apply custom CSS
echo "Applying custom CSS..."
cp ../assets/custom-style.css /usr/lib/node_modules/gancio/assets/style.css

# Restart Gancio service
echo "Restarting Gancio service..."
systemctl restart gancio

# Check service status
echo "Checking service status..."
if systemctl is-active --quiet gancio; then
    echo "✅ Gancio service is running"
else
    echo "❌ Gancio service failed to start!"
    echo "Check logs with: journalctl -u gancio -n 20"
    exit 1
fi

echo "=== Deployment completed successfully ==="
echo "Backup location: $BACKUP_DIR"
