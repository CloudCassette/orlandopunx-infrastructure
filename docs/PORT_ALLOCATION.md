# Port Allocation Strategy - Multiple Ghost Instances

## 🎯 **Updated Port Scheme for 4 Ghost Instances**

With Cloudflare tunnels, we use **internal-only ports** that are not exposed externally:

| Instance | Domain | Internal Port | Status | Purpose |
|----------|--------|---------------|--------|---------|
| **cloudcassette** | cloudcassette.blog | `127.0.0.1:2368` | ✅ Running | Personal blog |
| **orlandogirlsrockcamp** | orlandogirlsrockcamp.com | `127.0.0.1:2369` | 🔄 **Restore** | Girls Rock Camp |
| **tamtamthesandwichman** | tamtamthesandwichman.com | `127.0.0.1:2370` | 🔄 Deploy | Sandwich Man |
| **godlessamerica** | godless-america.com | `127.0.0.1:2371` | 🔄 Deploy | Godless America |

## 🔗 **Cloudflare Tunnel Architecture**

```
Internet → Cloudflare → Tunnel → nginx → Ghost Instance
   ↓           ↓         ↓        ↓         ↓
HTTPS      SSL Term   Local    Proxy    localhost:236X
```

### **Benefits**:
- ✅ **No external port exposure** (security)
- ✅ **SSL handled by Cloudflare** (automatic certificates)  
- ✅ **DDoS protection** via Cloudflare
- ✅ **Port conflicts impossible** (all internal)

## 🏗️ **Infrastructure Layers**

### **Layer 1: Ghost Containers (Internal)**
```yaml
cloudcassette-blog:     127.0.0.1:2368 → cloudcassette.blog
orlandogirlsrockcamp:   127.0.0.1:2369 → orlandogirlsrockcamp.com
tamtam-blog:            127.0.0.1:2370 → tamtamthesandwichman.com  
godlessamerica-blog:    127.0.0.1:2371 → godless-america.com
```

### **Layer 2: nginx Reverse Proxy**
- Routes traffic from tunnels to correct Ghost instance
- Handles static file caching and optimization
- Logs per-domain access and errors

### **Layer 3: Cloudflare Tunnels** 
- 5 tunnel containers (1 per domain + extras)
- SSL termination at Cloudflare edge
- Geographic load balancing

### **Layer 4: Portainer Management**
- Visual management of all containers
- Stack deployment and monitoring
- Volume and network management

## 🚀 **Current Status**

### ✅ **Ready to Deploy**
- **cloudcassette.blog**: ✅ Already running (port 2368)
- **orlandogirlsrockcamp.com**: 🔄 Ansible ready (port 2369)
- **tamtamthesandwichman.com**: 🔄 Ansible ready (port 2370)
- **godless-america.com**: 🔄 Ansible ready (port 2371)

### 📦 **Portainer Stack Names**
After deployment, you'll see these stacks in Portainer:
- `cloudcassette` (existing)
- `ghost-blog-ogrc` (new)
- `ghost-blog-tamtam` (new)
- `ghost-blog-godless` (new)

## 🔧 **Next Steps**

1. **Restore OGRC first** (you have the data):
   ```bash
   ansible-playbook playbooks/restore-orlandogirlsrockcamp.yml --ask-vault-pass
   ```

2. **Deploy additional instances** as needed:
   ```bash
   ansible-playbook playbooks/deploy-all-ghost-instances.yml --ask-vault-pass
   ```

**Perfect port isolation with Cloudflare tunnel security!** 🛡️
