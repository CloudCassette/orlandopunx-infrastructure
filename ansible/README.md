# Orlando Punx Infrastructure - Ansible

This directory contains Ansible configuration for managing the Orlando Punx server infrastructure, including Ghost blogs, Gancio event management, and web services.

## Structure

```
ansible/
├── ansible.cfg           # Ansible configuration
├── inventory/           
│   └── hosts.yml        # Server inventory
├── group_vars/          # Variables by group
│   ├── all.yml         # Global variables
│   ├── webservers.yml  # Web server variables  
│   ├── ghostservers.yml # Ghost server variables
│   └── vault.yml       # Encrypted secrets
├── playbooks/
│   └── site.yml        # Main playbook
├── roles/              # Ansible roles
│   ├── common/         # Basic server setup
│   ├── docker/         # Docker installation
│   ├── nginx/          # Web server configuration
│   ├── ghost/          # Ghost blog management
│   ├── gancio/         # Gancio event system
│   ├── postgresql/     # Database management
│   └── ssl/            # SSL certificate management
├── files/              # Static files
└── templates/          # Jinja2 templates
```

## Services Managed

### Current Infrastructure
- **nginx**: Reverse proxy and web server
- **Ghost**: Blog platform running in Docker containers
  - cloudcassette-blog (port 2368)
  - orlandogirlsrockcamp-blog (port 2369) - needs restoration
- **Gancio**: Event management system (port 13120)
- **PostgreSQL**: Database server
- **Docker**: Container runtime

### Domains
- **orlandopunx.com**: Main site (proxies to Gancio)
- **orlandogirlsrockcamp.com**: Ghost blog (needs restoration)

## Usage

### First Time Setup

1. **Encrypt the vault file**:
   ```bash
   ansible-vault encrypt ansible/group_vars/vault.yml
   ```

2. **Edit secrets** (update the placeholder values):
   ```bash
   ansible-vault edit ansible/group_vars/vault.yml
   ```

3. **Run the playbook**:
   ```bash
   cd ansible
   ansible-playbook playbooks/site.yml --ask-vault-pass
   ```

### Managing Secrets

All sensitive information is stored in `group_vars/vault.yml` and should be encrypted with `ansible-vault`. 

**Never commit unencrypted secrets to version control.**

### Restoring orlandogirlsrockcamp.com

To restore the orlandogirlsrockcamp.com Ghost instance:

1. Ensure the domain is configured in `group_vars/webservers.yml`
2. Update Ghost instances in `group_vars/ghostservers.yml`
3. Run the playbook to deploy the configuration
4. Restore Ghost content from backup

## Development

### Testing Changes

Run in check mode to validate without making changes:
```bash
ansible-playbook playbooks/site.yml --check --ask-vault-pass
```

### Adding New Services

1. Create a new role in `roles/`
2. Add the role to `playbooks/site.yml`
3. Add any necessary variables to appropriate `group_vars/` files

## Backup Integration

This Ansible configuration works with the existing backup scripts in the repository and can restore Ghost content from the backup packages.
