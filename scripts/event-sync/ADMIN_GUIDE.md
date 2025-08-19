# 🎸 Orlando Punk Events - Admin Guide

## 🔍 **Current Status**

✅ **Scraper Fixed**: Now captures real event titles instead of "Buy Tickets"  
✅ **Events Found**: 7 events are currently in Gancio with `status=pending`  
✅ **Automation Ready**: Credential-less automation is set up  

## 🚨 **Why You Don't See Events to Approve**

**The events ARE in your approval queue!** The issue is likely one of:

1. **🔍 Wrong admin panel section**: Look for:
   - "Pending Events" section
   - "Draft Events" section  
   - Events with status "pending" or "unapproved"

2. **🔐 User permissions**: Your account might not have admin permissions

3. **⚙️ Auto-approval enabled**: Gancio might be set to auto-approve events

## 📋 **Current Events in Approval Queue**

According to the API, these events are pending approval:
1. **GODS. with Here Here and mode.** - Aug 21, 2025 7:00 PM
2. **GODS. with Here Here and mode.** - Aug 24, 2025 7:00 PM  
3. **Fawn Fest with Special Guest, Fawn (debut show)...** - Aug 26, 2025 8:00 PM
4. **Sky Navy, Stella, No Clue, & Home and Away** - Aug 27, 2025 7:00 PM
5. **Keep, Leaving Time, and 0 Miles Per Hour** - Aug 28, 2025 6:00 PM
6. **Tele & the Ghost of our Lord Record Release Show** - Aug 29, 2025 8:00 PM
7. **Midhouse, Suisside, Hate Me For Life, and Animoxia** - Sep 1, 2025 7:00 PM

## 🤖 **Automated Sync Setup**

### Option 1: Environment Variables (Recommended)
```bash
# Set your password (replace with actual password)
export GANCIO_PASSWORD='your-actual-password'

# Run automated sync
cd /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync
source venv/bin/activate
python3 automated_sync_with_credentials.py
```

### Option 2: Edit .env File
```bash
# Edit the .env file
nano .env

# Add this line (replace with actual password):
GANCIO_PASSWORD=your-actual-password
```

### Option 3: Ansible Automation
```bash
# Run with Ansible (password via variable)
cd /home/cloudcassette/orlandopunx-infrastructure
ansible-playbook ansible/playbooks/sync-orlandopunx-events.yml -e "gancio_password=your-password"
```

## 📅 **Setting Up Cron Job**

To run automatically every 2 hours:
```bash
# Edit crontab
crontab -e

# Add this line:
0 */2 * * * cd /home/cloudcassette/orlandopunx-infrastructure/scripts/event-sync && source venv/bin/activate && GANCIO_PASSWORD='your-password' python3 automated_sync_with_credentials.py >> /home/cloudcassette/logs/orlandopunx-sync.log 2>&1
```

## 🔧 **Troubleshooting Commands**

### Check Gancio Status
```bash
python3 debug_gancio_status.py
```

### Run Fixed Scraper Only
```bash
python3 enhanced_multi_venue_sync.py
```

### Preview What Would Be Synced
```bash
python3 preview_fixed_events.py
```

### Check API Directly
```bash
# See all events
curl -s localhost:13120/api/events | jq '.[].title'

# See pending events
curl -s "localhost:13120/api/events?status=pending" | jq length

# See approved=false events  
curl -s "localhost:13120/api/events?approved=false" | jq length
```

## 📂 **File Structure**

```
scripts/event-sync/
├── enhanced_multi_venue_sync.py          # Fixed scraper (main)
├── automated_sync_with_credentials.py    # Automated sync
├── debug_gancio_status.py               # Debug tool
├── setup_automated_sync.sh              # Setup helper
├── .env                                 # Environment variables
└── ADMIN_GUIDE.md                       # This guide
```

## 🎯 **Next Steps**

1. **Find the approval queue in Gancio admin panel**
2. **Set up automated credentials** (choose option 1, 2, or 3 above)
3. **Test automated sync**: `python3 automated_sync_with_credentials.py`
4. **Set up cron job** for regular automation
5. **Verify events appear on orlandopunx.com** after approval

## 🆘 **Support**

If you're still not finding the approval queue:
1. Check Gancio documentation for your version
2. Look for "Moderation", "Review", or "Admin" sections
3. Check user permissions in Gancio settings
4. Consider if auto-approval is enabled in Gancio config
