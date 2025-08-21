# Conduit Venue Association Fix Guide

## 🚨 Problem
Conduit events are showing up in Gancio but have `null` place values, causing admin panel errors:
- Error: "An error occurred: can't access property 'name', o.place is null"
- Events appear in listings but can't be accessed
- Admin panel crashes when trying to view/edit these events

## 🎯 Quick Fix (Immediate Resolution)

### Step 1: Fix Existing Broken Events

```bash
cd scripts/event-sync

# Check what events need fixing (dry run)
python3 fix_conduit_venue_association.py

# Actually fix the problematic events
python3 fix_conduit_venue_association.py --fix
```

This will:
- ✅ Identify all events with null/missing venue associations
- 🎯 Specifically detect Conduit events using pattern matching
- 🔧 Associate them with the proper Conduit venue in Gancio
- ✅ Resolve the admin panel errors immediately

### Step 2: Prevent Future Issues

```bash
# Use the enhanced sync script going forward
python3 automated_sync_working_with_conduit_support.py
```

This enhanced script:
- ✅ Loads venue mappings directly from Gancio
- 🎯 Intelligently detects venues from event content
- 🔧 Ensures EVERY event has proper venue assignment
- ⚠️ Uses fallback venues if detection fails
- 📊 Reports venue assignments for verification

## 🔍 What the Fix Scripts Do

### `fix_conduit_venue_association.py`
- **Purpose**: Repair existing broken events
- **Detection**: Finds events with `place == null` or `placeId == null`  
- **Smart Matching**: Identifies Conduit events by content patterns
- **Safe Operation**: Dry-run mode by default, requires `--fix` flag

### `automated_sync_working_with_conduit_support.py`
- **Purpose**: Prevent future venue association issues
- **Multi-Venue**: Supports Will's Pub, Conduit, Stardust, Sly Fox, etc.
- **Dynamic Mapping**: Loads current venues from Gancio automatically
- **Intelligent Detection**: Pattern matching + fuzzy matching + content analysis
- **Mandatory Venues**: Cannot create events without proper venue association

## 📊 Verification

After running the fix, verify the results:

```bash
# Check that Conduit events now have proper venues
curl -s http://localhost:13120/api/events | grep -i conduit

# Or visit the Gancio admin panel - the errors should be gone
```

## 🚀 Going Forward

1. **Use the enhanced sync script** instead of the old one:
   ```bash
   # Instead of: python3 automated_sync_working.py
   # Use: python3 automated_sync_working_with_conduit_support.py
   ```

2. **Update GitHub Actions workflows** to use the new script

3. **Monitor for issues** - the new script will report any venue detection problems

## ⚡ Emergency Manual Fix Commands

If the automated fix doesn't work, you can use these manual commands:

```bash
# Show manual fix commands
python3 fix_conduit_venue_association.py --generate-commands
```

This generates SQL and curl commands you can run directly.

## 🎉 Expected Results

After the fix:
- ✅ No more admin panel errors
- ✅ All Conduit events properly associated with Conduit venue
- ✅ Events can be viewed/edited in admin panel
- ✅ Future syncs will maintain proper venue associations
- ✅ Clear reporting of venue assignments

The "Hot in Here: A 2000s Dance Party" event and all other Conduit events should now display properly with the Conduit venue tag visible!
