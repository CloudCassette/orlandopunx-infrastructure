# 🚀 OrlandoPunx.com Deployment Guide

Complete guide for deploying and maintaining the Orlando Punk Shows website infrastructure.

## 📋 Prerequisites

### System Requirements
- **OS**: Debian/Ubuntu Linux
- **Node.js**: v18+ (currently v20.19.4)
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 10GB minimum, 20GB recommended
- **Network**: Static IP with ports 80, 443, 13120 accessible

### Required Services
- **Gancio**: Event management platform
- **Nginx**: Web server and reverse proxy
- **Cloudflare**: CDN and SSL termination
- **Systemd**: Service management

## 🏗️ Fresh Installation

### 1. System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install additional dependencies
sudo apt install -y nginx certbot python3-certbot-nginx git
```

### 2. Gancio Installation
```bash
# Install Gancio globally
sudo npm install -g gancio

# Create gancio user and directories
sudo useradd -m -s /bin/bash gancio
sudo mkdir -p /var/lib/gancio
sudo chown gancio:gancio /var/lib/gancio
```

### 3. Configuration
```bash
# Copy configuration files
sudo cp configs/gancio/config.json /var/lib/gancio/config.json
sudo cp configs/systemd/gancio.service /etc/systemd/system/
sudo cp configs/nginx/orlandopunx.conf /etc/nginx/sites-available/

# Enable services
sudo systemctl daemon-reload
sudo systemctl enable gancio
sudo ln -s /etc/nginx/sites-available/orlandopunx.conf /etc/nginx/sites-enabled/
```

### 4. SSL Certificate
```bash
# Obtain SSL certificate
sudo certbot --nginx -d orlandopunx.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### 5. Deploy Customizations
```bash
# Deploy custom styling
cd gancio/themes/
./deploy-custom-styling.sh

# Deploy SEO improvements
cd ../../seo/
./deploy-seo-improvements.sh

# Start services
sudo systemctl start gancio nginx
```

## 🔄 Updates and Maintenance

### Gancio Updates
```bash
# Stop service
sudo systemctl stop gancio

# Backup current installation
sudo cp -r /usr/lib/node_modules/gancio /opt/backups/gancio-$(date +%Y%m%d)

# Update Gancio
sudo npm update -g gancio

# Redeploy customizations
cd /home/cloudcassette/orlandopunx-infrastructure
./gancio/themes/deploy-custom-styling.sh
./seo/deploy-seo-improvements.sh

# Restart service
sudo systemctl start gancio
```

### Security Updates
```bash
# System updates
sudo apt update && sudo apt upgrade -y

# SSL certificate renewal
sudo certbot renew

# Restart services if needed
sudo systemctl restart nginx gancio
```

## 🔍 Health Checks

### Service Status
```bash
# Check all services
sudo systemctl status gancio nginx

# Check Gancio accessibility
curl -I http://localhost:13120

# Check public website
curl -I https://orlandopunx.com
```

### SEO Status
```bash
# Check sitemap
curl https://orlandopunx.com/sitemap.xml

# Check robots.txt
curl https://orlandopunx.com/robots.txt

# Check RSS feed
curl https://orlandopunx.com/feed/rss
```

### Database Status
```bash
# Check database size
sudo du -sh /var/lib/gancio/gancio.sqlite

# Check recent events
sudo sqlite3 /var/lib/gancio/gancio.sqlite "SELECT title, start_datetime FROM events ORDER BY start_datetime DESC LIMIT 5;"
```

## 🆘 Troubleshooting

### Gancio Won't Start
```bash
# Check logs
sudo journalctl -u gancio -n 50

# Check configuration
sudo -u gancio gancio --check-config

# Reset to defaults
sudo cp configs/gancio/config.json.backup /var/lib/gancio/config.json
sudo systemctl restart gancio
```

### Website Not Accessible
```bash
# Check nginx status
sudo systemctl status nginx

# Check nginx configuration
sudo nginx -t

# Check firewall
sudo ufw status

# Check Cloudflare settings
# - DNS pointing to correct IP
# - SSL/TLS mode set to "Full"
# - Page Rules configured
```

### Database Issues
```bash
# Backup current database
sudo cp /var/lib/gancio/gancio.sqlite /opt/backups/gancio_emergency_$(date +%Y%m%d_%H%M%S).sqlite

# Check database integrity
sudo sqlite3 /var/lib/gancio/gancio.sqlite "PRAGMA integrity_check;"

# Restore from backup if needed
sudo systemctl stop gancio
sudo cp /opt/backups/gancio/latest/gancio.sqlite /var/lib/gancio/gancio.sqlite
sudo chown gancio:gancio /var/lib/gancio/gancio.sqlite
sudo systemctl start gancio
```

## 📊 Monitoring

### Key Metrics to Monitor
- **Uptime**: Service availability
- **Response Time**: Website performance
- **Disk Usage**: Database and log growth
- **Memory Usage**: Node.js memory consumption
- **Error Rates**: Application errors

### Automated Monitoring
```bash
# Set up monitoring script
cp monitoring/health-check.sh /opt/
sudo chmod +x /opt/health-check.sh

# Add to crontab
echo "*/5 * * * * /opt/health-check.sh" | sudo crontab -
```

### Manual Checks
```bash
# Weekly health check
./monitoring/weekly-report.sh

# Performance analysis
./monitoring/performance-check.sh

# SEO status report
./seo/generate-seo-report.sh
```

## 🔐 Security

### Regular Security Tasks
- Keep system packages updated
- Monitor failed login attempts
- Review SSL certificate expiration
- Check for unusual traffic patterns
- Update application dependencies

### Backup Strategy
- **Daily**: Database backup
- **Weekly**: Full system backup
- **Monthly**: Offsite backup verification
- **Before Updates**: Complete system snapshot

### Access Control
- SSH key authentication only
- Firewall rules for specific ports
- Regular user access review
- Service account permissions audit

---

*For emergency support, check logs first, then consult troubleshooting guides.*
