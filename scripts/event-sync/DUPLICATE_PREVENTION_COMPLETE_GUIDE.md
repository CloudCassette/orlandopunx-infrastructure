# 🧹 Gancio Duplicate Prevention & Cleanup Guide

## 🚨 Problem Summary
The Orlando Punk Events sync system was creating massive duplicates due to:
- Multiple active GitHub Actions workflows running simultaneously
- Weak duplicate detection (title-only matching) 
- Hidden events accumulating in approval queue

## ✅ Solution Implemented (2025-08-21)

### 1. Workflow Cleanup
**Disabled redundant sync workflows:**
- `DISABLED_debug-enhanced-sync.yml` (was: `debug-enhanced-sync.yml`)
- `DISABLED_debug-sync.yml` (was: `debug-sync.yml`)
- `DISABLED_emergency-debug.yml` (was: `emergency-debug.yml`)

**Active workflow:**
- `reliable-sync.yml` - Runs 3x daily (9am, 3pm, 9pm EST)

### 2. Database Cleanup Results
**Before cleanup:** 206 total events
- 32 visible events
- 174 hidden/duplicate events

**After cleanup:** 67 total visible events  
- ✅ Approved: 35 unique events
- 🗑️ Deleted: 139 duplicate events

**Major duplicates eliminated:**
- "Thursday Thinks Trivia": 16 → 1 copy
- "Hard Swingin' Country Soiree": 15 → 1 copy
- "DJ BMF": 14 → 1 copy
- And 26+ more duplicate types

## 🛠️ Tools Created

### `gancio_queue_manager.py`
Comprehensive search tool to find hidden/pending events:
- Scans API endpoints for approval queues
- Analyzes hidden events in database
- Scrapes admin pages for event counts

### `gancio_bulk_cleanup.py`
Bulk cleanup and approval tool:
- Analyzes duplicate events by title
- Creates cleanup plan (keep earliest, delete rest)
- Executes bulk approval and deletion
- Includes dry-run mode for safety

## 🔧 Usage

### Find Hidden Events
```bash
sudo -u gancio python3 gancio_queue_manager.py
```

### Clean Up Duplicates (Dry Run)
```bash
sudo -u gancio python3 gancio_bulk_cleanup.py
```

### Execute Cleanup (Live)
```bash
sudo -u gancio python3 gancio_bulk_cleanup.py --execute
```

## 🚀 Prevention Measures

### 1. Single Scheduled Workflow
Only `reliable-sync.yml` runs automatically:
- Schedule: 3x daily
- Includes connectivity checks
- Has basic duplicate detection

### 2. Improved Duplicate Detection
Current sync script (`automated_sync_working_multi_venue.py`) uses:
- Title-based duplicate checking
- Fetches existing events before sync
- Filters new events only

### 3. Available Enhancement Tools
- `enhanced_deduplication_guide.py` - Advanced fuzzy matching
- `comprehensive_duplicate_management.py` - Regular maintenance
- `simple_duplicate_analyzer.py` - Quick analysis

## 📊 Database Direct Access
```sql
-- Check event counts by visibility
sudo -u gancio sqlite3 /var/lib/gancio/gancio.sqlite "SELECT is_visible, COUNT(*) FROM events GROUP BY is_visible;"

-- Find duplicates
sudo -u gancio sqlite3 /var/lib/gancio/gancio.sqlite "SELECT title, COUNT(*) as count FROM events GROUP BY title HAVING count > 1 ORDER BY count DESC;"

-- Total events
sudo -u gancio sqlite3 /var/lib/gancio/gancio.sqlite "SELECT COUNT(*) FROM events;"
```

## 🎯 Future Maintenance
1. **Monthly**: Run duplicate analysis
2. **Before major sync changes**: Backup database
3. **After venue additions**: Check for new duplicate patterns
4. **Monitor**: GitHub Actions success rates

## 📝 Key Lessons
- **API limitations**: Hidden events don't appear in public API
- **Database direct access**: Required for comprehensive analysis  
- **Workflow isolation**: Single scheduled job prevents race conditions
- **Backup importance**: Always dry-run before bulk operations

## 🔗 Related Files
- `.github/workflows/reliable-sync.yml` - Main sync workflow
- `automated_sync_working_multi_venue.py` - Sync script
- `gancio_bulk_cleanup.py` - Cleanup tool
- `gancio_queue_manager.py` - Analysis tool
