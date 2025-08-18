# Ansible Infrastructure Setup Complete

## What's Been Created

I've successfully captured your current server configuration in Ansible and committed it to your infrastructure repository. Here's what was set up:

### Current Infrastructure Captured
- **nginx**: Reverse proxy configuration for orlandopunx.com → Gancio (port 13120)
- **Ghost**: Docker container setup (cloudcassette-blog on port 2368)
- **PostgreSQL**: Database service configuration  
- **Gancio**: Event management system
- **Docker**: Container management and volumes
- **SSL**: Certificate management (currently using snakeoil certs)

### Ansible Structure Created
```
ansible/
├── ansible.cfg              # Ansible configuration
├── inventory/hosts.yml      # Server inventory
├── group_vars/             # Configuration variables
│   ├── all.yml            # Global settings
│   ├── webservers.yml     # nginx & domain config
│   ├── ghostservers.yml   # Ghost instances config
│   └── vault.yml          # Secrets (unencrypted - needs setup)
├── playbooks/
│   ├── site.yml           # Main infrastructure playbook
│   ├── test-connection.yml # Basic connectivity test
│   └── restore-orlandogirlsrockcamp.yml # OGRC restoration
└── roles/                 # Service-specific configurations
    ├── common/            # Base server setup
    ├── docker/            # Docker installation
    ├── nginx/             # Web server config
    ├── ghost/             # Ghost blog management
    ├── gancio/            # Gancio event system
    ├── postgresql/        # Database management
    └── ssl/               # SSL certificates
```

## Next Steps for orlandogirlsrockcamp.com Restoration

### 1. Secure Your Secrets First
```bash
cd /home/cloudcassette/orlandopunx-infrastructure/ansible

# Edit the vault file and set real passwords
nano group_vars/vault.yml

# Encrypt the vault file
ansible-vault encrypt group_vars/vault.yml
```

### 2. Restore orlandogirlsrockcamp.com
```bash
# Run the restoration playbook
ansible-playbook playbooks/restore-orlandogirlsrockcamp.yml --ask-vault-pass
```

This will:
- Create nginx configuration for orlandogirlsrockcamp.com → Ghost (port 2369)
- Set up the Ghost container for the domain
- Create MySQL database for the Ghost instance
- Configure proper networking

### 3. Restore Ghost Content
After the infrastructure is running, you'll need to restore the actual Ghost content from your backup:

```bash
# Extract your backup if needed
tar -xzf ghost_recovery_package.tar.gz

# Import database content (example)
docker exec -i orlandogirlsrockcamp-mysql mysql -u ogrc_ghost -p orlandogirlsrockcamp < backup.sql

# Copy content files
docker cp backup_content/. orlandogirlsrockcamp-blog:/var/lib/ghost/content/
```

## Configuration Details

### Domain Setup
The configuration is ready for both domains:
- **orlandopunx.com**: Proxies to Gancio (port 13120) ✅ Current
- **orlandogirlsrockcamp.com**: Will proxy to Ghost (port 2369) 🔄 Ready to restore

### Ghost Instances
- **cloudcassette-blog**: Existing (port 2368) ✅ Captured
- **orlandogirlsrockcamp-blog**: Ready to restore (port 2369) 🔄 Configured

### Security
- Cloudflare IP ranges configured for real visitor IP
- Security headers implemented
- SSL termination ready (currently using snakeoil certs)

## Testing Your Setup

```bash
cd ansible/

# Test basic connectivity
ansible-playbook playbooks/test-connection.yml

# Test configuration (dry run)
ansible-playbook playbooks/site.yml --check --ask-vault-pass

# Deploy full configuration
ansible-playbook playbooks/site.yml --ask-vault-pass
```

## Repository Status
✅ All infrastructure code committed to git
✅ Vault file in .gitignore (won't commit secrets)
✅ Ready for orlandogirlsrockcamp.com restoration

Your infrastructure is now fully captured as code and ready for the Ghost restoration process!
