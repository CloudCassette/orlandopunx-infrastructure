# Custom Docker Configuration

## Important: Non-Standard Docker Location

This server uses a **custom Docker root directory** instead of the default `/var/lib/docker`:

**Docker Root Directory**: `/media/Steam Dock/docker_data`

### Impact on Infrastructure Management

1. **Volume Storage**: All Docker volumes are stored in `/media/Steam Dock/docker_data/volumes/`
2. **Container Data**: Container filesystems are in `/media/Steam Dock/docker_data/overlay2/`
3. **Images**: Docker images stored in `/media/Steam Dock/docker_data/image/`

### Current Ghost Infrastructure

**Existing Volumes**:
- `cloudcassette_ghost_content` → `/media/Steam Dock/docker_data/volumes/cloudcassette_ghost_content/_data`
- `cloudcassette_ghost_mysql` → `/media/Steam Dock/docker_data/volumes/cloudcassette_ghost_mysql/_data`
- `cloudcassette_fresh_ghost_content` → `/media/Steam Dock/docker_data/volumes/cloudcassette_fresh_ghost_content/_data`

**Running Container**:
- `cloudcassette-blog`: Ghost:latest on port 2368

### orlandogirlsrockcamp.com Status

❌ **No existing container or volumes found for orlandogirlsrockcamp.com**
❌ **No nginx configuration for orlandogirlsrockcamp.com domain**

This confirms the need for restoration from backup.

### Ansible Considerations

The Ansible configuration has been updated to:
1. ✅ Respect the custom Docker root directory
2. ✅ Properly configure Docker daemon.json
3. ✅ Create volumes in the correct location
4. ✅ Account for the Steam Dock mount point

### Backup Implications

When creating backups of Ghost content, the actual data is located at:
```
/media/Steam Dock/docker_data/volumes/[volume_name]/_data/
```

Not in the standard `/var/lib/docker/volumes/` location.
