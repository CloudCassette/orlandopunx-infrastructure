# Will's Pub to Gancio Sync

Automatically scrape events from Will's Pub (https://willspub.org) and sync them to your Gancio instance.

## 🚀 Quick Start

### Option 1: Manual Import (Recommended)
```bash
python3 willspub_manual_import.py
```
This creates formatted text files for easy copy/paste into your Gancio admin.

### Option 2: API Sync (If Gancio API is Fixed)
```bash
python3 willspub_to_gancio_final_working.py
```

### Option 3: Browser Automation (Advanced)
```bash
pip install selenium
python3 willspub_selenium_sync.py
```

## 📋 Scripts Included

1. **`willspub_manual_import.py`** - ⭐ **RECOMMENDED**
   - Scrapes events and creates formatted files
   - Perfect for manual copy/paste into Gancio admin
   - No API issues, full control over imports

2. **`willspub_to_gancio_final_working.py`**
   - Direct API integration (currently not working due to SPA limitations)
   - For when/if the API issues are resolved

3. **`willspub_selenium_sync.py`**
   - Browser automation using Selenium
   - Requires ChromeDriver installation

## 📦 Requirements

### Basic Requirements (Manual Import)
- Python 3.x
- `requests` library
- `beautifulsoup4` library

Install with:
```bash
pip install requests beautifulsoup4
```

### Advanced Requirements (Selenium)
- All basic requirements plus:
- `selenium` library
- ChromeDriver

Install with:
```bash
pip install selenium
# Download ChromeDriver from https://chromedriver.chromium.org/
```

## 🎯 Usage Examples

### Get 10 Latest Events (Manual Import)
```bash
python3 willspub_manual_import.py
# Enter "10" when prompted
```

### Get All Current Events
```bash
python3 willspub_manual_import.py
# Enter "50" or higher when prompted
```

## 📄 Output Files

The manual import script creates:
- **`willspub_events.txt`** - Formatted for copy/paste
- **`willspub_events.csv`** - Spreadsheet format
- **`willspub_events.json`** - JSON format for future use

## 🔧 Configuration

Edit the scripts to change:
- Gancio instance URL (currently: https://orlandopunx.com)
- Event limits
- Venue mappings

## 🎵 Supported Venues

- Will's Pub (placeId: 1)
- Uncle Lou's (placeId: 2)
- Lil' Indies (mapped to Will's Pub)

## 📅 Regular Usage

Run weekly or as needed:
```bash
cd willspub-gancio-sync
python3 willspub_manual_import.py
```

Then import the generated events manually through your Gancio admin panel.

## 🛠️ Troubleshooting

### Common Issues

1. **Import errors**: Install required packages
2. **No events found**: Check if Will's Pub website is accessible
3. **API errors**: Use manual import method instead

### Getting Help

The manual import method is most reliable. If you have issues:
1. Try the manual import script first
2. Check your internet connection
3. Verify Python and package installations

## 📝 Notes

- Events are scraped with all details: title, date, time, venue, price, description
- Manual approval recommended for quality control
- Script handles duplicate detection
- Respects website rate limits with built-in delays

## 🎉 Success Story

This toolset successfully:
- ✅ Scrapes all Will's Pub events with complete details
- ✅ Formats data perfectly for Gancio import
- ✅ Handles dates, times, prices, and descriptions
- ✅ Provides multiple import methods
- ✅ Maintains data quality and control

Perfect for keeping your Orlando punk scene calendar up to date! 🎸
