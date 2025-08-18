# 🎸 Orlando Punk Shows - Complete Infrastructure

This repository contains all infrastructure, configurations, scripts, and documentation for [OrlandoPunx.com](https://orlandopunx.com) - Orlando's digital poster wall for underground punk shows.

## 🎯 Site Overview

**URL**: https://orlandopunx.com  
**Platform**: Gancio (federated event management platform)  
**Purpose**: Digital poster wall for underground punk shows in Orlando, FL  
**Primary Venues**: Will's Pub, Uncle Lou's, and other local venues  

## 📁 Repository Structure

```
├── gancio/              # Gancio platform customizations
│   ├── themes/          # Custom CSS and styling
│   ├── configs/         # Gancio configuration files
│   └── plugins/         # Custom plugins and extensions
├── seo/                 # SEO optimization files and strategies
│   ├── implementations/ # Deployed SEO improvements
│   ├── analytics/       # Google Analytics and tracking
│   └── reports/         # SEO performance reports
├── scripts/             # Automation and integration scripts
│   ├── event-sync/      # Will's Pub event synchronization
│   ├── backup/          # Backup and restoration scripts
│   └── maintenance/     # System maintenance scripts
├── docs/                # Documentation and guides
│   ├── setup/           # Installation and setup guides
│   ├── api/             # API documentation
│   └── troubleshooting/ # Common issues and solutions
├── configs/             # System configuration files
│   ├── nginx/           # Web server configuration
│   ├── systemd/         # Service configurations
│   └── ssl/             # SSL certificate management
├── backups/             # Backup policies and restore procedures
└── monitoring/          # System monitoring and alerting
```

## 🚀 Quick Start

### For SEO Improvements
```bash
cd seo/implementations/
./deploy-seo-improvements.sh
```

### For Gancio Customizations
```bash
cd gancio/themes/
./deploy-custom-styling.sh
```

### For Event Synchronization
```bash
cd scripts/event-sync/
python willspub_to_gancio_sync.py
```

## 🎵 Current Features

### ✅ SEO Optimizations (Implemented)
- XML sitemap at `/sitemap.xml`
- Enhanced robots.txt with proper directives
- Dynamic structured data generation
- SEO-optimized CSS for better readability
- Google Analytics integration ready

### ✅ Visual Customizations (Implemented)
- Fixed image display (full flyers instead of cropped squares)
- Custom CSS overrides for better visual presentation
- Mobile-responsive improvements

### ✅ Event Integration (Implemented)
- Will's Pub event synchronization
- Automated event posting from external sources
- Event flyer optimization and display

## 🛠️ System Information

**Server**: 192.168.86.4  
**Port**: 13120 (internal), 443/80 (public via Cloudflare)  
**OS**: Debian GNU/Linux  
**Node.js**: v20.19.4  
**Gancio Version**: 1.4.4  
**Database**: SQLite (`/var/lib/gancio/gancio.sqlite`)  

## 📊 SEO Performance

### Current Status
- ✅ Sitemap: https://orlandopunx.com/sitemap.xml
- ✅ Robots.txt: https://orlandopunx.com/robots.txt
- ✅ RSS Feed: https://orlandopunx.com/feed/rss
- 🔄 Google Search Console: Setup needed
- 🔄 Google Analytics: Setup needed

### Target Keywords
- Orlando punk shows
- Orlando hardcore concerts
- Will's Pub events
- Orlando underground music
- Orlando music calendar
- DIY shows Orlando

## 🔧 Maintenance

### Daily Checks
- [ ] Gancio service status
- [ ] Event synchronization logs
- [ ] SSL certificate validity

### Weekly Tasks
- [ ] SEO performance review
- [ ] Backup verification
- [ ] Event data cleanup

### Monthly Tasks
- [ ] Security updates
- [ ] Performance optimization
- [ ] Analytics reporting

## 📈 Analytics & Monitoring

### Key Metrics
- Monthly active users
- Event page views
- RSS feed subscribers
- Search engine rankings
- Social media engagement

### Monitoring Tools
- Google Analytics (pending setup)
- Google Search Console (pending setup)
- System monitoring via systemd
- Custom alerting scripts

## 🤝 Contributing

### Making Changes
1. Create feature branch: `git checkout -b feature/description`
2. Test changes in staging environment
3. Update documentation
4. Submit pull request

### Deployment Process
1. Test all changes locally
2. Create backup of current state
3. Deploy to production
4. Verify functionality
5. Monitor for issues

## 🆘 Emergency Contacts

### System Issues
- Check service status: `sudo systemctl status gancio`
- View logs: `sudo journalctl -u gancio -f`
- Restart service: `sudo systemctl restart gancio`

### Backup & Recovery
- Database backup location: `/opt/backups/gancio/`
- Configuration backup: `/home/cloudcassette/gancio-customizations/backup/`
- Recovery procedures: `docs/troubleshooting/recovery.md`

## 🏷️ Version History

### v2.0 (Current - August 2025)
- Comprehensive SEO implementation
- Enhanced visual customizations
- Complete infrastructure documentation
- Automated event synchronization

### v1.0 (July 2025)
- Initial Gancio deployment
- Basic customizations
- Will's Pub integration
- SSL certificate setup

## 📧 Contact

**Email**: godlessamericarecords@gmail.com  
**Website**: https://orlandopunx.com  
**System Admin**: CloudCassette

---

*🎸 Supporting the Orlando punk scene since 2025! 🎸*

**Show your support by attending local shows and sharing events!**
<- Shows all content of event Test automated deployment Mon Aug 18 02:20:48 AM EDT 2025 -->
