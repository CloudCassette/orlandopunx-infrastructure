# Orlando Punx Infrastructure

**Infrastructure as Code + event automation for the Orlando Punx ecosystem** — Ghost blogs, Gancio events, and community services.

> **Status: maintenance mode.** Event sync workflows are **disabled or DRY_RUN by default** (see [Event Sync](#-event-sync-automation)); the repo has been dormant since September 2025. Live services (Gancio at `orlandopunx.com`, Ghost blogs) continue to run unchanged.

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
- **🎸 orlandogirlsrockcamp.com**: Ghost blog (port 2369) 📋 *ready for restoration*
- **🥪 tamtamthesandwichman.com**: Ghost blog (port 2370) 📋 *planned*
- **⚡ godless-america.com**: Ghost blog (port 2371) 📋 *planned*

## 🤖 **Event Sync Automation**

### **Automated Will's Pub → Gancio Pipeline**
```
Will's Pub Website → Python Scraper → Image Processing → Gancio API → orlandopunx.com
       ↓                    ↓              ↓             ↓            ↓
   Event listings      JSON extraction   Flyer upload   Event creation   Live events
```

### **Event Sources**
- **Will's Pub** — `willspub.org` (The Events Calendar markup), handled directly in `fixed_sync_improved.py`
- **Orlando Weekly → Stardust Video & Coffee** — CitySpark events widget via `src/scrapers/orlando_weekly.py`
- **Orlando Weekly → My Sister's House** — same CitySpark widget; search results are filtered to cards whose **venue text** mentions "My Sister's House" (the widget also matches titles/descriptions, so events hosted elsewhere — e.g. Mood Lounge — are excluded)
- **Flyers** — Orlando Weekly events carry a flyer `image_url` resolved from the CitySpark payload (`MediumImg` → `LargeImg` → first `Images[].url`), attached to Gancio events via the API's `image_url`/`image_name` fields (server-side download + JPEG resize via sharp)

> **⚠️ My Sister's House has no Gancio place yet**, so its events are dropped
> with a `⚠️` note until the venue is created in the Gancio admin (the fuzzy
> `places` lookup then picks it up automatically) **or** the
> `ORLANDO_WEEKLY_MSH_PLACE_ID` env var is set. Stardust resolves automatically
> to place id 4 (a `ORLANDO_WEEKLY_STARDUST_PLACE_ID` override is also
> supported). Events are never assigned to the wrong venue as a fallback.

> **DRY_RUN:** live submissions are enabled. While hardening, runs were
> DRY_RUN-only (scrape + dedup validation without writes); a manual
> dry-run is still available via the workflow's `dry_run` dispatch input.

### **Current State (as of 2026-10)**
- **GitHub Actions**: `fixed-sync.yml` runs daily at 9am EST and **submits events live** (new events land unconfirmed in the admin approval queue); a manual dry-run is available via workflow_dispatch
- **Cron**: manual event-sync cron entry is **disabled** on the server (superseded by the Actions workflow)
- **Manual trigger**: `src/sync/fixed_sync_improved.py` (the only maintained sync runner) and `scripts/event-sync/sync_wrapper_fixed.sh`
- **Duplicates**: a one-off Selenium cleanup removed duplicate events; the identity-verifier tooling is archived under the `pre-cleanup-2026-10-11` tag
- Do **not** re-enable sync without checking current Gancio state first

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
- **Cloudflare tunnels**: Tunnel instances for secure access

### **Services**
- **nginx**: Reverse proxy (Cloudflare tunnel termination)
- **PostgreSQL**: Database server (system service)
- **Gancio**: Event management (system service on the homelab server)
- **Ghost instances**: Multiple blog platforms (containerized)

## 📁 **Repository Structure** (as of 2026-10 cleanup)

```
├── src/                    # Python package (entry: sync-events, serve-gallery)
│   ├── scrapers/           #   conduit.py, songkick.py, willspub.py, orlando_weekly.py
│   ├── sync/               #   main.py, fixed_sync_improved.py, deduplication.py
│   ├── gallery/            #   server.py (flyer gallery)
│   └── utils/
├── ansible/                # Infrastructure as Code
│   ├── inventory/          # Server definitions
│   ├── group_vars/         # Configuration variables (vault refs, no plaintext)
│   ├── roles/              # cloudflare, docker, gancio, ghost, nginx, ...
│   └── playbooks/          # Deployment scripts
├── scripts/
│   ├── event-sync/         #   only CI/cron- referenced files remain (6)
│   ├── deploy-changes.sh
│   ├── sync-events         #   entry point → src.sync.main
│   └── serve-gallery       #   entry point → src.gallery.server
├── seo/                    # nuxt config, robots.txt, sitemap, deploy scripts
├── gancio/                 # Gancio customizations + seo-improvements
├── tools/                  # debug/ + monitoring/ helpers
├── monitoring/             # health-check.sh
├── docs/                   # API, deployment, port allocation, CI guides
├── configs/                # templates only (config.json.template, systemd units)
├── backups/                # infrastructure snapshots
└── .github/workflows/      # 5 active (+ archived experiments)
```

**History cleanup note (2026-10-11):** ~270 one-off cleanup/debug scripts, HTML dumps, and experiment variants were removed from the tree; old `scripts/event-sync/` experiments and removal tooling are preserved under the `pre-cleanup-2026-10-11` tag.

## 🔐 **Credentials**

- `config.py` is **gitignored and purged from history** — never commit credentials
- Use `config_example.py` as a template; put real values in the environment or GitHub Actions secrets (`GANCIO_EMAIL`, `GANCIO_PASSWORD`, `GANCIO_BASE_URL`, `DISCORD_WEBHOOK_URL`)
- Ansible vault keeps all service passwords out of plaintext (`group_vars/*.yml` use `vault_*` references)

## 🚀 **Quick Start**

### **Test Current Infrastructure**
```bash
cd ansible/
ansible-playbook playbooks/test-connection.yml
```

### **Run Event Sync Manually (dry run)**
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
# View current events in Gancio
curl -s "https://orlandopunx.com/api/events" | jq '.[].title'
```

## 🔗 **Related Repositories**

- **[homelab](http://192.168.86.4:3000/cloudcassette/homelab)**: homelab server configs (Docker Compose services, restic backup jobs, scripts) — also on [GitHub](https://github.com/CloudCassette/homelab)
- **This repo**: mirrored to self-hosted **Forgejo** at `http://192.168.86.4:3000/cloudcassette/orlandopunx-infrastructure` (`ssh://git@192.168.86.4:2222`), with GitHub as origin

## 📚 **Documentation**

### **Infrastructure**
- [PORT_ALLOCATION.md](docs/PORT_ALLOCATION.md) - Port strategy for multiple Ghost instances
- [CURRENT_PORTAINER_STACKS.md](docs/CURRENT_PORTAINER_STACKS.md) - Stack analysis
- [DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) - Server and Gancio deployment
- [API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md) - Gancio/API reference
- [ANSIBLE_SETUP_COMPLETE.md](ANSIBLE_SETUP_COMPLETE.md) - Setup completion guide

### **Automation**
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [GITHUB_SECRETS_SETUP.md](GITHUB_SECRETS_SETUP.md) - GitHub Actions configuration

## ⚡ **Status: Maintenance Mode**

**✅ Core services active** (Gancio, blog infrastructure)  
**⏸️ Event automation paused** — sync workflows disabled/DRY_RUN pending network-stability work  
**🧹 Repo cleaned** — 2026-10-11 purge of one-off scripts and credentials
