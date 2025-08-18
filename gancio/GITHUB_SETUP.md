# GitHub Repository Setup Guide

## Step 1: Create the Repository on GitHub

1. **Go to GitHub**: Visit https://github.com/CloudCassette
2. **Create new repository**: Click the green "New" button
3. **Repository settings**:
   - Repository name: `gancio-customizations`
   - Description: `Custom configurations and styling for Gancio installation at OrlandoPunx.com`
   - Visibility: **Private** (recommended - contains configuration data)
   - **DO NOT** check any of these boxes:
     - [ ] Add a README file
     - [ ] Add .gitignore  
     - [ ] Choose a license
   
   *(We already have these files in our local repository)*

4. **Click "Create repository"**

## Step 2: Connect Local Repository to GitHub

After creating the repository, GitHub will show you setup instructions. Follow the **"push an existing repository from the command line"** section:

```bash
# Navigate to your local repository (if not already there)
cd ~/gancio-customizations

# Add GitHub as remote origin
git remote add origin https://github.com/CloudCassette/gancio-customizations.git

# Rename branch to main (modern Git convention)
git branch -M main

# Push everything to GitHub
git push -u origin main
```

## Step 3: Authentication

When prompted for credentials during the push:

### Option A: Personal Access Token (Recommended)
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Name it: "Gancio Customizations Access"
4. Select scopes: `repo` (Full control of private repositories)
5. Click "Generate token"
6. **Copy the token immediately** (you won't see it again)

When prompted:
- Username: `CloudCassette`
- Password: `[paste your personal access token]`

### Option B: SSH Keys (More Secure)
If you prefer SSH authentication:
```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "cloudcassette@orlandopunx.com"

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Copy public key to clipboard
cat ~/.ssh/id_ed25519.pub
```

Then add the public key to GitHub at https://github.com/settings/keys

## Step 4: Verify Setup

After successful push:
```bash
# Check remote configuration
git remote -v

# Check repository status
git status

# View commit history
git log --oneline
```

## Step 5: Update Remote URL (if using SSH)

If you set up SSH keys, update the remote URL:
```bash
git remote set-url origin git@github.com:CloudCassette/gancio-customizations.git
```

## Next Steps

- Your repository is now backed up on GitHub
- You can clone it from other machines
- Collaborate with others (if you make it public or invite collaborators)
- Use GitHub Issues for tracking tasks
- Set up GitHub Actions for automated deployments (optional)

## Security Notes

- This repository is set to private to protect configuration data
- The .gitignore file prevents sensitive files from being committed
- Configuration templates have sensitive data removed
- Always review files before committing sensitive information
