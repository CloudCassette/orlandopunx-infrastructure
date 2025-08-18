# Infrastructure Backup - 2025-08-18T15:48:15Z

## Critical: Custom Docker Configuration
- Docker Root Directory: /media/Steam Dock/docker_data
- Steam Dock Mount: /dev/sdc1       1.8T 1015G  725G  59% /media/Steam Dock
- Volume Location: /media/Steam Dock/docker_data/volumes/

## Current Running Containers
- cloudcassette-blog: Ghost:latest (Up 5 days, port 2368)

## Current Services Status
- nginx: active (proxying orlandopunx.com to Gancio:13120)
- docker: active (custom root: /media/Steam Dock/docker_data)
- postgresql: active (cluster 15-main)
- gancio: active (port 13120)

## Existing Ghost Volumes (Steam Dock location)
- cloudcassette_ghost_content: /media/Steam Dock/docker_data/volumes/cloudcassette_ghost_content/_data
- cloudcassette_ghost_mysql: /media/Steam Dock/docker_data/volumes/cloudcassette_ghost_mysql/_data  
- cloudcassette_fresh_ghost_content: /media/Steam Dock/docker_data/volumes/cloudcassette_fresh_ghost_content/_data

## System Info
- OS: Debian 12.11
- Architecture: x86_64
- Hostname: cassette-lab
- Kernel: 6.1.0-37-amd64

## orlandogirlsrockcamp.com Status ❌
- Container: NOT FOUND (needs restoration)
- Volume: NOT FOUND (will be created in Steam Dock location)
- nginx config: NOT FOUND (will be created by Ansible)
- Domain: NOT CONFIGURED (needs nginx site)

## Next Steps for Restoration
1. Run: ansible-playbook playbooks/restore-orlandogirlsrockcamp.yml --ask-vault-pass
2. This will create volumes in: /media/Steam Dock/docker_data/volumes/
3. Restore Ghost content from backup to new volumes
4. Configure DNS to point orlandogirlsrockcamp.com to this server
