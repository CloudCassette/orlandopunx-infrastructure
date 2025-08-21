# 🗄️ GitHub Workflows Archive

This directory contains historical/experimental workflows that are no longer active but preserved for reference.

## 📁 Directory Structure

### `sync-experiments/`
Experimental event sync workflows from the duplicate cleanup project (August 2025):
- Various attempts to solve sync reliability issues
- Different approaches to duplicate prevention
- Debug and testing workflows
- **Outcome**: Replaced by single `reliable-sync.yml` workflow

## 🚀 Active Workflows
The following workflows are currently active in `.github/workflows/`:
- `reliable-sync.yml` - Main event sync (3x daily)
- `deploy-to-server.yml` - Infrastructure deployment  
- `validate-changes.yml` - PR validation
- `test-discord.yml` - Discord integration testing
- `simple-diagnostic.yml` - System diagnostics

## 📋 Cleanup History
- **2025-08-21**: Moved 10 DISABLED_* workflows to archive
- **Issue**: Multiple sync workflows causing duplicate events (174 hidden duplicates)
- **Solution**: Single reliable workflow + comprehensive cleanup tools
- **Result**: Clean event database (67 visible events, 0 duplicates)

## 💡 Usage
If you need to reference old workflows:
1. Check this archive first
2. Workflows here are **historical only** - don't move them back without review
3. Consider creating new workflows rather than restoring old ones
