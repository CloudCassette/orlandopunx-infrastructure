#!/bin/bash

# Orlando Punk Shows - Backup Strategy Script
# Creates comprehensive backups of all system components

BACKUP_BASE="/opt/backups/orlandopunx"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

create_backup_dirs() {
    mkdir -p "$BACKUP_BASE/$DATE"/{database,configs,uploads,logs,customizations}
}

backup_database() {
    log "Backing up Gancio database..."
    
    # Stop Gancio to ensure consistent backup
    systemctl stop gancio
    
    # Copy database
    cp /var/lib/gancio/gancio.sqlite "$BACKUP_BASE/$DATE/database/"
    
    # Create SQL dump for portability
    sqlite3 /var/lib/gancio/gancio.sqlite .dump > "$BACKUP_BASE/$DATE/database/gancio_dump.sql"
    
    # Restart Gancio
    systemctl start gancio
    
    log "Database backup completed"
}

backup_configs() {
    log "Backing up configuration files..."
    
    # Gancio config
    cp /var/lib/gancio/config.json "$BACKUP_BASE/$DATE/configs/"
    
    # Nginx config
    cp /etc/nginx/sites-available/orlandopunx.conf "$BACKUP_BASE/$DATE/configs/"
    
    # Systemd service
    cp /etc/systemd/system/gancio.service "$BACKUP_BASE/$DATE/configs/"
    
    # SSL certificates
    if [ -d /etc/letsencrypt/live/orlandopunx.com ]; then
        cp -r /etc/letsencrypt/live/orlandopunx.com "$BACKUP_BASE/$DATE/configs/ssl/"
    fi
    
    log "Configuration backup completed"
}

backup_uploads() {
    log "Backing up uploaded files..."
    
    if [ -d /var/lib/gancio/uploads ]; then
        cp -r /var/lib/gancio/uploads "$BACKUP_BASE/$DATE/"
    fi
    
    log "Uploads backup completed"
}

backup_customizations() {
    log "Backing up customizations..."
    
    # Gancio customizations
    if [ -d /home/cloudcassette/gancio-customizations ]; then
        cp -r /home/cloudcassette/gancio-customizations "$BACKUP_BASE/$DATE/customizations/"
    fi
    
    # Infrastructure repo
    if [ -d /home/cloudcassette/orlandopunx-infrastructure ]; then
        cp -r /home/cloudcassette/orlandopunx-infrastructure "$BACKUP_BASE/$DATE/customizations/"
    fi
    
    # Custom static files
    if [ -f /usr/lib/node_modules/gancio/static/sitemap.xml ]; then
        mkdir -p "$BACKUP_BASE/$DATE/customizations/static"
        cp /usr/lib/node_modules/gancio/static/sitemap.xml "$BACKUP_BASE/$DATE/customizations/static/"
        cp /usr/lib/node_modules/gancio/static/robots.txt "$BACKUP_BASE/$DATE/customizations/static/"
        cp /usr/lib/node_modules/gancio/static/seo-*.{css,js} "$BACKUP_BASE/$DATE/customizations/static/" 2>/dev/null || true
    fi
    
    log "Customizations backup completed"
}

backup_logs() {
    log "Backing up important logs..."
    
    # Gancio logs
    if [ -d /var/lib/gancio/logs ]; then
        cp -r /var/lib/gancio/logs "$BACKUP_BASE/$DATE/"
    fi
    
    # System logs (last 7 days)
    journalctl -u gancio --since "7 days ago" > "$BACKUP_BASE/$DATE/logs/gancio_journal.log"
    journalctl -u nginx --since "7 days ago" > "$BACKUP_BASE/$DATE/logs/nginx_journal.log"
    
    # Nginx access logs (last 7 days)
    if [ -f /var/log/nginx/orlandopunx_access.log ]; then
        tail -10000 /var/log/nginx/orlandopunx_access.log > "$BACKUP_BASE/$DATE/logs/nginx_access.log"
    fi
    
    log "Logs backup completed"
}

create_manifest() {
    log "Creating backup manifest..."
    
    cat > "$BACKUP_BASE/$DATE/MANIFEST.txt" << MANIFEST
Orlando Punk Shows Backup
Created: $(date)
Server: $(hostname)
Gancio Version: $(gancio --version 2>/dev/null || echo "Unknown")

Contents:
- Database: Gancio SQLite database and SQL dump
- Configs: System and application configurations
- Uploads: Event flyers and media files
- Customizations: Custom themes, SEO improvements, scripts
- Logs: Recent system and application logs

Restore Instructions:
1. Install Gancio and dependencies
2. Stop gancio service
3. Restore database from database/gancio.sqlite
4. Restore configs to appropriate locations
5. Restore uploads to /var/lib/gancio/uploads
6. Deploy customizations using scripts
7. Start services and verify functionality

For detailed restore procedures, see backups/restore-guide.md
MANIFEST

    log "Manifest created"
}

compress_backup() {
    log "Compressing backup..."
    
    cd "$BACKUP_BASE"
    tar -czf "orlandopunx_backup_$DATE.tar.gz" "$DATE/"
    
    if [ $? -eq 0 ]; then
        rm -rf "$DATE"
        log "Backup compressed to orlandopunx_backup_$DATE.tar.gz"
    else
        log "ERROR: Backup compression failed"
        return 1
    fi
}

cleanup_old_backups() {
    log "Cleaning up old backups..."
    
    find "$BACKUP_BASE" -name "orlandopunx_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete
    
    log "Old backups cleaned up (retention: $RETENTION_DAYS days)"
}

verify_backup() {
    log "Verifying backup..."
    
    local backup_file="$BACKUP_BASE/orlandopunx_backup_$DATE.tar.gz"
    
    if [ ! -f "$backup_file" ]; then
        log "ERROR: Backup file not found"
        return 1
    fi
    
    # Test archive integrity
    if ! tar -tzf "$backup_file" >/dev/null 2>&1; then
        log "ERROR: Backup file is corrupted"
        return 1
    fi
    
    local size=$(du -h "$backup_file" | cut -f1)
    log "Backup verification passed (size: $size)"
}

send_notification() {
    local status="$1"
    local message="OrlandoPunx.com backup $status at $(date)"
    
    # Email notification (if configured)
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "Backup Notification" godlessamericarecords@gmail.com
    fi
    
    log "$message"
}

main() {
    log "Starting backup process..."
    
    create_backup_dirs
    
    if backup_database && backup_configs && backup_uploads && backup_customizations && backup_logs; then
        create_manifest
        
        if compress_backup && verify_backup; then
            cleanup_old_backups
            send_notification "completed successfully"
            log "Backup process completed successfully"
            return 0
        else
            send_notification "failed during compression/verification"
            log "ERROR: Backup process failed during compression/verification"
            return 1
        fi
    else
        send_notification "failed during data collection"
        log "ERROR: Backup process failed during data collection"
        return 1
    fi
}

main "$@"
