# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Repository Overview

Orlando Punx Infrastructure manages the complete technical ecosystem for the Orlando punk music scene, including event management, blog platforms, and automated event synchronization. This is a **production system** serving the live Orlando punk community.

## Key Architecture Components

### Core Services Stack
- **Gancio** (port 13120): Event management system for orlandopunx.com
- **Ghost blogs**: Multiple instances (ports 2368-2371) for different punk community sites
- **nginx**: Reverse proxy handling Cloudflare tunnel termination  
- **PostgreSQL**: System-level database server
- **Event Sync Pipeline**: Automated scraping and API integration from venue websites

### Infrastructure Management
- **Ansible**: Infrastructure as Code in `/ansible/` directory
- **Docker**: Custom root at `/media/Steam Dock/docker_data` (1.8TB storage)
- **Portainer**: Container management UI at https://localhost:9443
- **Cloudflare Tunnels**: 5 tunnel instances for secure public access

### Automation Systems
- **Event Scraping**: Python-based scrapers for Will's Pub and Uncle Lou's venues
- **GitHub Actions**: CI/CD workflows for event synchronization 
- **Cron Jobs**: Scheduled event sync every 2 hours
- **Image Processing**: Automated event flyer download and gallery management

## Essential Commands

### Development Setup
```bash
# Initialize development environment
make setup                    # Install dependencies and pre-commit hooks
make dev-install             # Development dependencies only
pip install -e .[dev]       # Alternative manual install
```

### Code Quality
```bash
make format                  # Black + isort formatting
make lint                   # flake8, mypy, shellcheck
make test                   # Run pytest with coverage
make check                  # Run all quality checks (format + lint + test)
make pre-commit             # Run pre-commit hooks manually
```

### Event Synchronization
```bash
# Manual event sync (primary method)
cd scripts/event-sync/
./sync_wrapper_fixed.sh

# Check sync status
tail -f scripts/event-sync/sync_summary.txt

# View current events in Gancio API
curl -s "https://orlandopunx.com/api/events" | jq '.[].title'
```

### Infrastructure Management
```bash
# Test Ansible connectivity
cd ansible/
ansible-playbook playbooks/test-connection.yml

# Deploy all Ghost blog instances
ansible-playbook playbooks/deploy-all-ghost-instances.yml --ask-vault-pass

# Run infrastructure health checks
./monitoring/health-check.sh
```

### Service Management
```bash
# Check core services
sudo systemctl status gancio nginx

# Gancio service operations
sudo systemctl restart gancio
sudo journalctl -u gancio -f         # Follow logs

# Test Gancio accessibility
curl -I http://localhost:13120
curl -I https://orlandopunx.com
```

## Event Sync Architecture

The event synchronization system is **critical production infrastructure** that keeps the Orlando punk community informed:

### Key Components
- **Primary Script**: `scripts/event-sync/automated_sync_working.py`
- **Wrapper**: `scripts/event-sync/sync_wrapper_fixed.sh` (handles cron environment)
- **Scraper**: `enhanced_multi_venue_sync.py` (Will's Pub + Uncle Lou's)
- **Authentication**: Uses web form login, not API authentication

### Environment Requirements
```bash
# Required environment variables
export GANCIO_EMAIL="godlessamericarecords@gmail.com"
export GANCIO_PASSWORD="<vault_password>"
export GANCIO_URL="http://localhost:13120"
```

### Automation Schedule
- **Cron**: Every 2 hours (24/7)
- **GitHub Actions**: 9am, 3pm, 9pm EST (backup)
- **Manual**: Run `sync_wrapper_fixed.sh` anytime

## Project Structure Philosophy

### Scripts Directory (`scripts/`)
- **Current Working Files**: `*_working.py`, `*_fixed.sh`
- **Legacy/Backup**: `*_backup.py`, `*_old.py` (archived via `make archive`)
- **Active Automation**: Focus on `automated_sync_working.py` and wrapper

### Source Directory (`src/`) - New Structure
- **scrapers/**: Venue-specific scraping modules
- **sync/**: Gancio API integration
- **gallery/**: Event flyer management
- **utils/**: Shared utilities

### Ansible Directory (`ansible/`)
- **playbooks/**: Deployment and management scripts
- **roles/**: Service-specific configurations  
- **group_vars/**: Configuration variables (including encrypted vault)
- **inventory/**: Server definitions

## Important Operational Notes

### Authentication Patterns
- **Gancio**: Uses web form authentication (`/login` endpoint), NOT API auth
- **Working Method**: Session-based cookies after successful form login
- **GitHub Actions**: Uses repository secrets for credentials

### Database Considerations
- **Gancio**: SQLite database at `/var/lib/gancio/gancio.sqlite`
- **Ghost**: Each instance has separate database
- **PostgreSQL**: System-level service for infrastructure

### Venue-Specific Details
- **Will's Pub**: Primary venue (place_id = 1 in Gancio)
- **Uncle Lou's**: Secondary venue (Songkick integration)
- **Event Detection**: Smart deduplication prevents duplicate events
- **Flyer Processing**: Automatic image download and gallery upload

### File Management
- **Archive Strategy**: Use `make archive` to clean old files safely
- **Docker Data**: Large volume at `/media/Steam Dock/docker_data`
- **Backup Location**: `/opt/backups/` for system backups

## Testing Guidelines

### Event Sync Testing
```bash
# Test scraper independently
cd scripts/event-sync/
python3 enhanced_multi_venue_sync.py

# Test full sync process
./sync_wrapper_fixed.sh

# Check for duplicate detection
grep -i "existing events skipped" sync_summary.txt
```

### Infrastructure Testing
```bash
# Test Ansible playbooks (dry run)
ansible-playbook playbooks/site.yml --check --ask-vault-pass

# Test service connectivity
ansible-playbook playbooks/test-connection.yml

# Validate configurations
sudo nginx -t
sudo -u gancio gancio --check-config
```

## Development Workflow

### For Event Sync Changes
1. Test scrapers independently first
2. Use manual sync wrapper for validation
3. Check existing events detection logic
4. Verify image processing functionality
5. Monitor sync_summary.txt for results

### For Infrastructure Changes
1. Test in Ansible check mode first
2. Use development/staging approach for major changes
3. Always backup before infrastructure modifications
4. Validate service restart procedures

### For SEO/Frontend Changes
1. Test responsive design across devices
2. Validate structured data markup
3. Check robots.txt and sitemap.xml functionality
4. Verify Cloudflare integration remains intact

## Emergency Procedures

### Event Sync Failure
```bash
# Check recent logs
journalctl -u gancio -n 100
tail -f scripts/event-sync/sync_summary.txt

# Manual authentication debug
cd scripts/event-sync/
python3 check_gancio_admin_fixed.py

# Restart services
sudo systemctl restart gancio
```

### Service Outage
```bash
# Check all critical services
sudo systemctl status gancio nginx
curl -I https://orlandopunx.com

# Emergency restart sequence
sudo systemctl restart nginx
sudo systemctl restart gancio

# Check Cloudflare tunnel status (if needed)
```

This infrastructure serves the **live Orlando punk music community** - treat all changes with appropriate care and testing.
