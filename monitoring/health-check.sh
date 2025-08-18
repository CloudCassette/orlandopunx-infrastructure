#!/bin/bash

# Orlando Punk Shows - Health Check Script
# Monitors system health and sends alerts if issues are detected

LOG_FILE="/var/log/orlandopunx-health.log"
ALERT_EMAIL="godlessamericarecords@gmail.com"
WEBHOOK_URL=""  # Optional Discord/Slack webhook

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

check_gancio() {
    if ! systemctl is-active --quiet gancio; then
        log "ERROR: Gancio service is not running"
        return 1
    fi
    
    if ! curl -s -f http://localhost:13120/api/health >/dev/null; then
        log "ERROR: Gancio health check failed"
        return 1
    fi
    
    return 0
}

check_nginx() {
    if ! systemctl is-active --quiet nginx; then
        log "ERROR: Nginx service is not running"
        return 1
    fi
    
    return 0
}

check_ssl() {
    local days_until_expiry=$(openssl x509 -enddate -noout -in /etc/letsencrypt/live/orlandopunx.com/cert.pem 2>/dev/null | cut -d= -f2 | xargs -I {} date -d {} +%s)
    local current_date=$(date +%s)
    local days_left=$(( (days_until_expiry - current_date) / 86400 ))
    
    if [ $days_left -lt 30 ]; then
        log "WARNING: SSL certificate expires in $days_left days"
        return 1
    fi
    
    return 0
}

check_disk() {
    local usage=$(df /var/lib/gancio | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ $usage -gt 80 ]; then
        log "WARNING: Disk usage is at ${usage}%"
        return 1
    fi
    
    return 0
}

check_memory() {
    local gancio_memory=$(ps -o pid,vsz,comm -C node | grep gancio | awk '{sum+=$2} END {print sum/1024}')
    
    if [ $(echo "$gancio_memory > 500" | bc -l) -eq 1 ]; then
        log "WARNING: Gancio using ${gancio_memory}MB memory"
        return 1
    fi
    
    return 0
}

check_website() {
    local response=$(curl -s -o /dev/null -w "%{http_code}" https://orlandopunx.com)
    
    if [ "$response" != "200" ]; then
        log "ERROR: Website returning HTTP $response"
        return 1
    fi
    
    return 0
}

check_seo_files() {
    local sitemap_status=$(curl -s -o /dev/null -w "%{http_code}" https://orlandopunx.com/sitemap.xml)
    local robots_status=$(curl -s -o /dev/null -w "%{http_code}" https://orlandopunx.com/robots.txt)
    
    if [ "$sitemap_status" != "200" ] || [ "$robots_status" != "200" ]; then
        log "ERROR: SEO files not accessible (sitemap: $sitemap_status, robots: $robots_status)"
        return 1
    fi
    
    return 0
}

send_alert() {
    local message="$1"
    
    # Email alert (if mail is configured)
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "OrlandoPunx.com Alert" "$ALERT_EMAIL"
    fi
    
    # Webhook alert (if configured)
    if [ -n "$WEBHOOK_URL" ]; then
        curl -s -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 OrlandoPunx.com Alert: $message\"}" \
            "$WEBHOOK_URL"
    fi
}

main() {
    local errors=0
    local warnings=0
    
    log "Starting health check..."
    
    if ! check_gancio; then
        ((errors++))
        send_alert "Gancio service check failed"
    fi
    
    if ! check_nginx; then
        ((errors++))
        send_alert "Nginx service check failed"
    fi
    
    if ! check_website; then
        ((errors++))
        send_alert "Website accessibility check failed"
    fi
    
    if ! check_seo_files; then
        ((warnings++))
    fi
    
    if ! check_ssl; then
        ((warnings++))
    fi
    
    if ! check_disk; then
        ((warnings++))
    fi
    
    if ! check_memory; then
        ((warnings++))
    fi
    
    if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
        log "All checks passed ✓"
    else
        log "Health check completed with $errors errors and $warnings warnings"
    fi
    
    # Auto-restart services if critical errors
    if [ $errors -gt 0 ]; then
        log "Attempting service recovery..."
        systemctl restart gancio nginx
        sleep 10
        
        if check_website && check_gancio && check_nginx; then
            log "Service recovery successful"
            send_alert "Services automatically recovered"
        else
            log "Service recovery failed - manual intervention required"
            send_alert "CRITICAL: Service recovery failed - manual intervention required"
        fi
    fi
}

main "$@"
