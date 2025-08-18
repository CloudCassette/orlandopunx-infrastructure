# 🔑 GitHub Secrets Setup Guide

To enable automated deployment from GitHub to your server, you need to configure SSH access secrets.

## 🎯 Why Do We Need Secrets?

GitHub Actions run on GitHub's servers, not your local machine. To deploy to your server, GitHub needs:
- Your server's IP address
- SSH credentials to connect securely
- Permission to run deployment commands

These are stored as encrypted "secrets" in your GitHub repository.

## 🚀 Step-by-Step Setup

### 1. Go to Repository Settings
- Navigate to: https://github.com/CloudCassette/orlandopunx-infrastructure
- Click the **"Settings"** tab (in the repository menu bar)
- In the left sidebar, click **"Secrets and variables"** → **"Actions"**

### 2. Add These Four Secrets

Click **"New repository secret"** for each of these:

#### SECRET 1: `SERVER_HOST`
- **Name**: `SERVER_HOST`
- **Value**: `192.168.86.4`
- **Purpose**: Your server's IP address

#### SECRET 2: `SERVER_USER`
- **Name**: `SERVER_USER`  
- **Value**: `cloudcassette`
- **Purpose**: SSH username

#### SECRET 3: `SERVER_SSH_KEY`
- **Name**: `SERVER_SSH_KEY`
- **Value**: Copy the ENTIRE private key from below (including BEGIN/END lines)
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAACmFlczI1Ni1jdHIAAAAGYmNyeXB0AAAAGAAAABCE/lq7gP
LMusRxWqzU35uNAAAAEAAAAAEAAAAzAAAAC3NzaC1lZDI1NTE5AAAAIFF5gb8r+pd++3wM
JrupZ6Y99RA0YBsYv01uuyeHPX3XAAAAoGQxFK4zLd1rG2jo9tGh6oPJ+3aCcmGs4Edudw
C8+u1unQyGDKbqZDUIDmUj5CDOV9SI8eEt8x52iSo1NAiUpiyZzsb6adnfrZN3vt0nuos7
fjF9wgiZwQJUQ5XSwm0d4QkjFNns/IcCGCqv/Eu5eiDkkReCeFUsPLLc6wGHq64zuE5cd8
JUXovB9qziSXtBF9lBCeSvtl36U+m4vq0gwU0=
-----END OPENSSH PRIVATE KEY-----
```
- **Purpose**: Private SSH key for authentication

#### SECRET 4: `SERVER_PORT`
- **Name**: `SERVER_PORT`
- **Value**: `22`
- **Purpose**: SSH port (standard port)

### 3. Test the Setup

After adding all secrets, you can test by:

1. **Make a small change** to any file in the repository
2. **Commit and push** to the main branch
3. **Go to the "Actions" tab** to watch the deployment
4. **Check your server** to see if changes were applied

## 🔍 How It Works

Once secrets are configured:

1. **You push to GitHub** → GitHub Action triggers
2. **GitHub connects to your server** using the SSH key  
3. **Pulls latest code** to `/home/cloudcassette/orlandopunx-infrastructure`
4. **Runs deployment script** based on what changed
5. **Restarts services** if needed
6. **Reports success/failure**

## 🛡️ Security Notes

- **Secrets are encrypted** by GitHub and only available during Action runs
- **Private key never appears** in logs or output
- **Only repository admins** can view/edit secrets
- **Keys are scoped** to this specific repository

## 🔧 Testing Deployment

Once secrets are added, test with a simple change:

```bash
# Edit README (or any file) with a small change
echo "<!-- Test deployment $(date) -->" >> README.md

# Commit and push
git add README.md
git commit -m "🧪 Test automated deployment"
git push origin main

# Watch the deployment in GitHub Actions tab
```

## ⚠️ Troubleshooting

### "Host key verification failed"
- The server's SSH host key isn't recognized
- Solution: GitHub Action will add it automatically on first run

### "Permission denied (publickey)"
- SSH key might be incorrect or not properly formatted
- Solution: Double-check the `SERVER_SSH_KEY` includes full key with BEGIN/END lines

### "Connection timed out" 
- Server might not be accessible from GitHub's servers
- Solution: Check if your server allows connections from external IPs

### "Command not found"
- Deployment script might not be executable
- Solution: The script will automatically make itself executable

## 🎸 Success!

Once working, you'll see:
- ✅ **Automatic deployments** on every push to main
- ✅ **Quality validation** on every pull request  
- ✅ **Deployment logs** in GitHub Actions
- ✅ **Health checks** after each deployment

**Your Orlando punk shows infrastructure will be fully automated!** 🤘

---

*For help with this setup, check the deployment logs in GitHub Actions or run `./scripts/deploy-changes.sh` manually on the server.*
