# Orlando Punx Infrastructure

**Infrastructure as Code for Orlando Punx ecosystem** - Ghost blogs, Gancio events, automated event sync, and community services.

## 🏗️ **Architecture Overview**

### **Cloudflare Tunnel Architecture**
```
Internet → Cloudflare Edge → Tunnel → nginx → Services
   ↓            ↓            ↓        ↓        ↓  
HTTPS      SSL/DDoS      Local    Proxy   Ghost/Gancio
```

### **Current Services**
- **🎸 orlandopunx.com**: Gancio event system (port 13120) ✅ **Active**
- **📝 cloudcassette.blog**: Ghost blog (port 2368) ✅ **Active**
- **🎸 orlandogirlsrockcamp.com**: Ghost blog (port 2369) ✅ **Active**
- **🥪 tamtamthesandwichman.com**: Ghost blog (port 2370) 📋 *Planned*
- **⚡ godless-america.com**: Ghost blog (port 2371) 📋 *Planned*

## 🤖 **Event Sync Automation**

### **Automated Will's Pub → Gancio Pipeline**
```
Will's Pub Website → Python Scraper → Image Processing → Gancio API → orlandopunx.com
       ↓                    ↓              ↓             ↓            ↓
   Event listings      JSON extraction   Flyer upload   Event creation   Live events
```

### **Automation Schedule**
- **Cron Jobs**: Every 2 hours (24/7 monitoring)
- **GitHub Actions**: 9am, 3pm, 9pm EST (redundant backup)
- **Manual Trigger**: `scripts/event-sync/sync_wrapper_fixed.sh`

### **Features**
- 🎯 **Smart Event Detection**: Prevents duplicate events
- 🖼️ **Automatic Flyer Upload**: Downloads and uploads event images
- 🔄 **Multi-source Scraping**: Will's Pub + Uncle Lou's (Songkick)
- 📧 **Error Notifications**: Automated alerts on sync failures
- 🎨 **Flyer Gallery**: Permanent web gallery for all event flyers

## 🛠️ **Infrastructure Stack**

### **Container Management**
- **Docker**: Custom root at `/media/Steam Dock/docker_data` (1.8TB)
- **Portainer**: Web UI at https://localhost:9443
- **Cloudflare tunnels**: 5 tunnel instances for secure access

### **Services**
- **nginx**: Reverse proxy (Cloudflare tunnel termination)
- **PostgreSQL**: Database server (system service)
- **Gancio**: Event management (system service)
- **Ghost instances**: Multiple blog platforms (containerized)

### **Automation Services**
- **Event Sync**: Python-based scraping and API integration
- **Image Processing**: Automated flyer download and upload
- **GitHub Actions**: CI/CD for event sync workflows
- **Cron Jobs**: Scheduled event synchronization

## 📁 **Repository Structure**

```
├── ansible/                 # Infrastructure as Code
│   ├── inventory/          # Server definitions
│   ├── group_vars/         # Configuration variables
│   ├── roles/              # Service configurations
│   └── playbooks/          # Deployment scripts
├── scripts/                # Automation scripts
│   ├── event-sync/         # Event automation system
│   │   ├── willspub_scraper_fixed.py
│   │   ├── sync_to_gancio_fixed.py
│   │   ├── sync_wrapper_fixed.sh
│   │   └── automated_sync_with_images.py
│   └── ...
├── configs/                # Legacy configurations
├── docs/                   # Documentation
├── backups/                # Infrastructure snapshots
├── .github/workflows/      # GitHub Actions automation
└── gancio/                 # Gancio customizations
```

## 🚀 **Quick Start**

### **Test Current Infrastructure**
```bash
cd ansible/
ansible-playbook playbooks/test-connection.yml
```

### **Run Event Sync Manually**
```bash
cd scripts/event-sync/
./sync_wrapper_fixed.sh
```

### **Deploy All Ghost Instances**
```bash
cd ansible/
ansible-playbook playbooks/deploy-all-ghost-instances.yml --ask-vault-pass
```

### **Monitor Event Sync Status**
```bash
# Check recent sync results
tail -f scripts/event-sync/sync_summary.txt

# View current events in Gancio
curl -s "https://orlandopunx.com/api/events" | jq '.[].title'
```

## 🔗 **Related Repositories**

- **[CloudCassette/homelab](https://github.com/CloudCassette/homelab)**: Terraform infrastructure provisioning
- **This repo**: Ansible service configuration and event automation

## 📚 **Documentation**

### **Infrastructure**
- [PORT_ALLOCATION.md](docs/PORT_ALLOCATION.md) - Port strategy for multiple Ghost instances
- [CLOUDFLARE_TUNNELS.md](docs/CLOUDFLARE_TUNNELS.md) - Tunnel architecture details  
- [CURRENT_PORTAINER_STACKS.md](docs/CURRENT_PORTAINER_STACKS.md) - Stack analysis
- [ANSIBLE_SETUP_COMPLETE.md](ANSIBLE_SETUP_COMPLETE.md) - Setup completion guide

### **Automation**
- [scripts/event-sync/FINAL_TEST_RESULTS.md](scripts/event-sync/FINAL_TEST_RESULTS.md) - Event sync test results
- [scripts/event-sync/SCRAPER_FIX_SUMMARY.md](scripts/event-sync/SCRAPER_FIX_SUMMARY.md) - Scraper fixes and improvements
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md) - GitHub Actions configuration

## ⚡ **Status: Fully Operational**

**✅ All core services are active and stable**  
**🤖 Event automation running reliably**  
**🎸 Orlando punk rock community infrastructure complete!**

---

*Last updated: August 19, 2025 - Infrastructure now includes full event automation pipeline*
