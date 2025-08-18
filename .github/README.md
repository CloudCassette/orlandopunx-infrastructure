# 🤖 GitHub Actions for Orlando Punk Shows

This directory contains automated workflows for the Orlando Punk Shows infrastructure.

## 🔄 Workflows

### 1. `deploy-to-server.yml` - Automatic Deployment
**Trigger**: Push to `main` branch  
**Purpose**: Automatically deploy changes to the production server

**What it does:**
- Pulls latest code to the server
- Deploys SEO improvements if changed
- Updates favicon if changed  
- Deploys Gancio customizations if changed
- Restarts services if configuration changed
- Runs health checks
- Logs deployment status

### 2. `validate-changes.yml` - Quality Assurance
**Trigger**: Push to `main` or Pull Request  
**Purpose**: Validate code quality and catch issues

**What it checks:**
- SEO file validity (sitemap XML, robots.txt format)
- Asset integrity (favicon, CSS files)
- Script syntax and executability
- Documentation completeness
- Basic security checks
- Markdown linting

## 🔧 Setup Requirements

### GitHub Secrets
To use the deployment workflow, configure these secrets in your GitHub repository:

1. **`SERVER_HOST`** - Server IP address (e.g., `192.168.86.4`)
2. **`SERVER_USER`** - SSH username (e.g., `cloudcassette`)
3. **`SERVER_SSH_KEY`** - Private SSH key for server access
4. **`SERVER_PORT`** - SSH port (default: 22)
5. **`SLACK_WEBHOOK_URL`** - Optional: Slack webhook for notifications
6. **`DISCORD_WEBHOOK_URL`** - Optional: Discord webhook for notifications

### Setting up Secrets
1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each secret with its corresponding value

### SSH Key Setup
To get the SSH private key:
```bash
# On the server, display the private key
cat ~/.ssh/id_ed25519_github

# Copy the entire output (including BEGIN/END lines) as SERVER_SSH_KEY secret
```

## 📱 Manual Deployment

You can also trigger deployments manually:

### Via GitHub Interface
1. Go to Actions tab in GitHub
2. Select "Deploy Orlando Punk Shows Infrastructure" 
3. Click "Run workflow"
4. Select branch and click "Run workflow"

### Via Server Command Line
```bash
# Run the deployment script directly on the server
cd /home/cloudcassette/orlandopunx-infrastructure
./scripts/deploy-changes.sh
```

## 🔍 Monitoring Deployments

### GitHub Actions Interface
- View deployment logs in the Actions tab
- Check for failed deployments
- Review validation results

### Server Logs
```bash
# View deployment logs
tail -f /var/log/orlandopunx-deployment.log

# Check specific deployment
grep "deploy-20250818" /var/log/orlandopunx-deployment.log
```

### Health Checks
```bash
# Run manual health check
./monitoring/health-check.sh

# Check service status
systemctl status gancio nginx
```

## 🚨 Troubleshooting

### Deployment Failures
1. Check GitHub Actions logs for error details
2. SSH to server and check service status
3. Review deployment logs: `/var/log/orlandopunx-deployment.log`
4. Run manual health check

### Common Issues
- **SSH connection failed**: Check `SERVER_HOST`, `SERVER_USER`, and `SERVER_SSH_KEY`
- **Permission denied**: Ensure SSH key has proper permissions
- **Service restart failed**: Check Gancio configuration and logs
- **Website inaccessible**: Verify nginx configuration and SSL certificates

### Recovery Steps
```bash
# Restore previous working state
git checkout HEAD~1
./scripts/deploy-changes.sh

# Or restore from backup
sudo systemctl stop gancio
sudo cp /opt/backups/gancio/latest/* /var/lib/gancio/
sudo systemctl start gancio
```

## 📈 Benefits

### Automated Deployment
- **Instant updates**: Changes go live automatically
- **Consistent process**: Same deployment steps every time  
- **Error detection**: Automatic validation and health checks
- **Rollback capability**: Easy to revert problematic changes

### Quality Assurance  
- **Code validation**: Catch syntax errors and issues
- **Documentation checks**: Ensure docs stay up-to-date
- **Security scanning**: Basic security issue detection
- **Asset validation**: Verify files are correct format

### Monitoring & Logging
- **Deployment history**: Track what changed when
- **Health monitoring**: Automatic service health checks
- **Notification system**: Get alerts on deployment status
- **Audit trail**: Complete log of all changes

---

## 🎸 Supporting the Orlando Punk Scene with Professional DevOps! 🎸

*These workflows ensure OrlandoPunx.com stays reliable and up-to-date automatically.*
