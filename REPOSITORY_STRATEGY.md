# Multi-Repository Infrastructure Strategy

## Repository Roles & Responsibilities

### 🏠 [CloudCassette/homelab](https://github.com/CloudCassette/homelab)
**Purpose**: Infrastructure Provisioning (Terraform)
- **Focus**: Cloud resources, VMs, networking, base infrastructure
- **Technology**: Terraform + HCL
- **Scope**: Multi-environment, scalable infrastructure
- **Contains**: Ghost module, provider configurations, variables

### 🎸 [CloudCassette/orlandopunx-infrastructure](current repo)
**Purpose**: Configuration Management (Ansible) 
- **Focus**: Application deployment, service configuration
- **Technology**: Ansible + YAML
- **Scope**: Orlando Punx specific services and sites
- **Contains**: nginx, Ghost, Gancio, Portainer roles

## Integration Strategy

### Terraform → Ansible Flow
1. **Terraform** provisions the base infrastructure
2. **Ansible** configures services and applications  
3. **Portainer** provides runtime container management

### Repository Cross-References
```yaml
# In homelab repo outputs.tf
output "server_ip" {
  value = module.ghost.server_ip
}

# In orlandopunx-infrastructure ansible/inventory/hosts.yml
orlandopunx-server:
  ansible_host: "{{ terraform.outputs.server_ip }}"
```

## Current Infrastructure Stack

### Layer 1: Base Infrastructure (Terraform)
- Server provisioning
- Network configuration
- Base Docker setup

### Layer 2: Service Configuration (Ansible)
- nginx reverse proxy setup
- Ghost blog configuration
- Gancio event management
- SSL certificate management
- Portainer container management

### Layer 3: Runtime Management (Portainer)
- Container monitoring and updates
- Volume management
- Network administration
- Template-based deployments

## Service Matrix

| Service | Terraform | Ansible | Portainer |
|---------|-----------|---------|-----------|
| Ghost | ✅ Module | ✅ Config | ✅ Runtime |
| nginx | ❌ | ✅ Config | ✅ Monitor |
| Gancio | ❌ | ✅ Config | ✅ Runtime |
| Portainer | ❌ | ✅ Deploy | ✅ Self-manage |
| SSL | ❌ | ✅ Manage | ❌ |

## Benefits of This Approach

### Separation of Concerns
- **Terraform**: "What infrastructure do I need?"
- **Ansible**: "How should services be configured?"
- **Portainer**: "How are containers running right now?"

### Disaster Recovery
- Terraform can rebuild infrastructure
- Ansible can reconfigure services
- Portainer can restore runtime state

### Team Collaboration  
- Infrastructure engineers work in homelab repo
- Application teams work in service-specific repos
- Operations teams use Portainer for day-to-day management

## Recommended Workflow

### New Service Deployment
1. Add Terraform module in homelab repo
2. Create Ansible role in appropriate service repo
3. Deploy via Ansible playbook
4. Monitor and manage via Portainer

### orlandogirlsrockcamp.com Restoration
1. ✅ Infrastructure exists (current server)
2. ✅ Ansible configuration ready
3. 🔄 Run restoration playbook
4. 🔄 Monitor via Portainer

This strategy maintains clear boundaries while enabling powerful integrations between your infrastructure layers.
