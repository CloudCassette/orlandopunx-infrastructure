# Orlando Punx Infrastructure

**Infrastructure as Code for Orlando Punx ecosystem** - Ghost blogs, Gancio events, and community services.

## 🏗️ **Architecture Overview**

### **Cloudflare Tunnel Architecture**
```
Internet → Cloudflare Edge → Tunnel → nginx → Services
   ↓            ↓            ↓        ↓        ↓  
HTTPS      SSL/DDoS      Local    Proxy   Ghost/Gancio
```

### **Current Services**
- **🎸 orlandopunx.com**: Gancio event system (port 13120)
- **📝 cloudcassette.blog**: Ghost blog (port 2368) ✅
- **🎸 orlandogirlsrockcamp.com**: Ghost blog (port 2369) 🔄 *Ready for restoration*
- **🥪 tamtamthesandwichman.com**: Ghost blog (port 2370) 📋 *Planned*
- **⚡ godless-america.com**: Ghost blog (port 2371) 📋 *Planned*

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

## 📁 **Repository Structure**

```
├── ansible/                 # Infrastructure as Code
│   ├── inventory/          # Server definitions
│   ├── group_vars/         # Configuration variables
│   ├── roles/              # Service configurations
│   └── playbooks/          # Deployment scripts
├── configs/                # Legacy configurations
├── docs/                   # Documentation
├── scripts/                # Automation scripts
└── backups/                # Infrastructure snapshots
```

## 🚀 **Quick Start**

### **Test Current Infrastructure**
```bash
cd ansible/
ansible-playbook playbooks/test-connection.yml
```

### **Restore orlandogirlsrockcamp.com**
```bash
cd ansible/
ansible-vault encrypt group_vars/vault.yml  # First time only
ansible-playbook playbooks/restore-orlandogirlsrockcamp.yml --ask-vault-pass
```

### **Deploy All Ghost Instances**
```bash
cd ansible/
ansible-playbook playbooks/deploy-all-ghost-instances.yml --ask-vault-pass
```

## 🔗 **Related Repositories**

- **[CloudCassette/homelab](https://github.com/CloudCassette/homelab)**: Terraform infrastructure provisioning
- **This repo**: Ansible service configuration and deployment

## 📚 **Documentation**

- [PORT_ALLOCATION.md](docs/PORT_ALLOCATION.md) - Port strategy for multiple Ghost instances
- [CLOUDFLARE_TUNNELS.md](docs/CLOUDFLARE_TUNNELS.md) - Tunnel architecture details  
- [CURRENT_PORTAINER_STACKS.md](docs/CURRENT_PORTAINER_STACKS.md) - Stack analysis
- [ANSIBLE_SETUP_COMPLETE.md](ANSIBLE_SETUP_COMPLETE.md) - Setup completion guide

## ⚡ **Status: Ready for Ghost Restoration**

**Infrastructure as code complete and safely committed to git.** 
**orlandogirlsrockcamp.com restoration can proceed!** 🎸✨
