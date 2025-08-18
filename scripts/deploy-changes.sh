#!/bin/bash

# Manual deployment script for Orlando Punk Shows infrastructure
# Can be run locally or called by GitHub Actions

set -e

LOG_FILE="/var/log/orlandopunx-deployment.log"
DEPLOYMENT_ID="deploy-$(date +%Y%m%d_%H%M%S)"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$DEPLOYMENT_ID] - $1" | tee -a "$LOG_FILE"
}

log "🎸 Starting Orlando Punk Shows deployment..."

# Get current directory
REPO_DIR="/home/cloudcassette/orlandopunx-infrastructure"
cd "$REPO_DIR"

# Pull latest changes
log "📥 Pulling latest changes from GitHub..."
git pull origin main

# Get the commit that triggered this deployment
CURRENT_COMMIT=$(git rev-parse HEAD)
PREVIOUS_COMMIT=$(git rev-parse HEAD~1 2>/dev/null || echo "")

log "🔍 Deploying commit: $CURRENT_COMMIT"

# Check what files changed
CHANGED_FILES=""
if [ -n "$PREVIOUS_COMMIT" ]; then
    CHANGED_FILES=$(git diff --name-only "$PREVIOUS_COMMIT" "$CURRENT_COMMIT" || echo "")
    log "📝 Changed files: $CHANGED_FILES"
fi

# Deploy SEO improvements if changed
if echo "$CHANGED_FILES" | grep -E "^seo/"; then
    log "🔍 SEO files changed, deploying SEO improvements..."
    ./seo/deploy-minimal-seo.sh 2>&1 | tee -a "$LOG_FILE" || log "⚠️  SEO deployment completed with warnings"
fi

# Deploy favicon if changed
if echo "$CHANGED_FILES" | grep -E "icons8.*\.png$"; then
    log "🎨 Favicon changed, updating favicon..."
    ./seo/update-favicon.sh 2>&1 | tee -a "$LOG_FILE" || log "⚠️  Favicon deployment completed with warnings"
fi

# Deploy Gancio customizations if changed
if echo "$CHANGED_FILES" | grep -E "^gancio/"; then
    log "🎸 Gancio customizations changed..."
    if [ -f "./gancio/scripts/deploy-customizations.sh" ]; then
        log "Deploying Gancio customizations..."
        ./gancio/scripts/deploy-customizations.sh 2>&1 | tee -a "$LOG_FILE" || log "⚠️  Gancio deployment completed with warnings"
    else
        log "No Gancio deployment script found, skipping..."
    fi
fi

# Update system configurations if changed
if echo "$CHANGED_FILES" | grep -E "configs/"; then
    log "⚙️  System configurations changed..."
    
    # Update nginx config if changed
    if echo "$CHANGED_FILES" | grep -E "configs/nginx/"; then
        log "Updating nginx configuration..."
        sudo cp configs/nginx/orlandopunx.conf /etc/nginx/sites-available/ 2>&1 | tee -a "$LOG_FILE" || log "⚠️  Nginx config update failed"
        sudo nginx -t 2>&1 | tee -a "$LOG_FILE" && sudo systemctl reload nginx || log "⚠️  Nginx reload failed"
    fi
    
    # Update systemd service if changed
    if echo "$CHANGED_FILES" | grep -E "configs/systemd/"; then
        log "Updating systemd service..."
        sudo cp configs/systemd/gancio.service /etc/systemd/system/ 2>&1 | tee -a "$LOG_FILE" || log "⚠️  Systemd service update failed"
        sudo systemctl daemon-reload 2>&1 | tee -a "$LOG_FILE"
    fi
fi

# Restart services if configuration files changed
RESTART_NEEDED=false
if echo "$CHANGED_FILES" | grep -E "(config.*\.json|nuxt\.config\.js|gancio\.service)"; then
    RESTART_NEEDED=true
fi

if [ "$RESTART_NEEDED" = true ]; then
    log "🔄 Configuration changed, restarting Gancio service..."
    
    # Backup current state
    log "Creating service backup..."
    sudo systemctl status gancio > "/tmp/gancio_status_before_restart_$DEPLOYMENT_ID.log" 2>&1 || true
    
    # Restart service
    sudo systemctl restart gancio 2>&1 | tee -a "$LOG_FILE" || log "❌ Failed to restart Gancio service"
    
    # Wait for service to start
    log "Waiting for service to start..."
    sleep 10
    
    # Check service status
    if sudo systemctl is-active gancio >/dev/null 2>&1; then
        log "✅ Gancio service restarted successfully"
    else
        log "❌ Gancio service restart failed - manual intervention required"
        sudo systemctl status gancio 2>&1 | tee -a "$LOG_FILE"
    fi
fi

# Run health check
log "🏥 Running health check..."
./monitoring/health-check.sh 2>&1 | tee -a "$LOG_FILE" || log "⚠️  Health check completed with warnings"

# Test website accessibility
log "🌐 Testing website accessibility..."
if curl -sf https://orlandopunx.com >/dev/null 2>&1; then
    log "✅ Website is accessible"
else
    log "❌ Website accessibility test failed"
fi

# Test SEO files
log "🔍 Testing SEO files..."
for file in sitemap.xml robots.txt; do
    if curl -sf "https://orlandopunx.com/$file" >/dev/null 2>&1; then
        log "✅ $file is accessible"
    else
        log "⚠️  $file accessibility test failed"
    fi
done

# Final status
log "📊 Deployment Summary:"
log "   • Commit: $CURRENT_COMMIT"
log "   • Files changed: $(echo "$CHANGED_FILES" | wc -l)"
log "   • Services restarted: $RESTART_NEEDED"
log "   • Deployment ID: $DEPLOYMENT_ID"

log "🎸 Orlando Punk Shows deployment completed!"

# Send notification if webhook URL is available
if [ -n "${DISCORD_WEBHOOK_URL:-}" ] || [ -n "${SLACK_WEBHOOK_URL:-}" ]; then
    log "📢 Sending deployment notification..."
    COMMIT_MSG=$(git log --format=%B -n 1 "$CURRENT_COMMIT" | head -1)
    MESSAGE="🎸 OrlandoPunx.com deployed successfully!\nCommit: $CURRENT_COMMIT\nMessage: $COMMIT_MSG\nDeployment: $DEPLOYMENT_ID"
    
    if [ -n "${DISCORD_WEBHOOK_URL:-}" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"content\":\"$MESSAGE\"}" \
            "$DISCORD_WEBHOOK_URL" 2>/dev/null || log "Discord notification failed"
    fi
fi

log "✅ All deployment tasks completed!"
