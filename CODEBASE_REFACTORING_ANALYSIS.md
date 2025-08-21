# Orlando Punx Infrastructure - Codebase Refactoring Analysis

## Current Structure Analysis

### 🔍 **Major Issues Identified**

1. **Massive Script Redundancy** (120+ scripts in `scripts/event-sync/`)
   - 15+ variations of sync scripts (`automated_sync_*`, `enhanced_*`, etc.)
   - 8+ duplicate scrapers (`willspub_scraper_*`, `songkick_scraper_*`)
   - 10+ debugging/diagnostic scripts with overlapping functionality
   - Multiple backup versions (`*_backup.py`, `*_fixed.py`)

2. **Poor Organization**
   - Core functionality mixed with debug tools
   - No clear separation between production vs development tools
   - Documentation scattered across multiple directories
   - Virtual environment committed to repository

3. **Workflow Proliferation** (15+ GitHub Actions workflows)
   - Multiple debug workflows with similar functionality
   - Backup and outdated workflow versions
   - No clear workflow naming conventions

## 🎯 **Proposed New Directory Structure**

```
orlandopunx-infrastructure/
├── README.md                           # Main project overview
├── CONTRIBUTING.md                     # Development guidelines
├── pyproject.toml                      # Python project configuration
├── requirements.txt                    # Production dependencies  
├── requirements-dev.txt                # Development dependencies
├── .gitignore                          # Updated gitignore
├── .pre-commit-config.yaml            # Pre-commit hooks
├── .github/
│   └── workflows/
│       ├── sync-events.yml             # Main event sync workflow
│       ├── deploy-infrastructure.yml   # Deployment workflow
│       ├── validate-changes.yml        # PR validation
│       └── debug-emergency.yml         # Emergency debugging only
├── src/                                # Core source code
│   ├── __init__.py
│   ├── scrapers/                       # Event data scrapers
│   │   ├── __init__.py
│   │   ├── base.py                     # Base scraper class
│   │   ├── willspub.py                 # Will's Pub scraper
│   │   ├── conduit.py                  # Conduit scraper
│   │   └── songkick.py                 # Songkick scraper
│   ├── sync/                           # Gancio sync functionality
│   │   ├── __init__.py
│   │   ├── client.py                   # Gancio API client
│   │   ├── deduplication.py            # Event deduplication
│   │   ├── venue_validation.py         # Venue assignment logic
│   │   └── image_upload.py             # Flyer image handling
│   ├── gallery/                        # Flyer gallery server
│   │   ├── __init__.py
│   │   ├── server.py                   # Main gallery server
│   │   └── templates/                  # HTML templates
│   └── utils/                          # Shared utilities
│       ├── __init__.py
│       ├── config.py                   # Configuration management
│       ├── logging.py                  # Logging utilities
│       └── validation.py               # Data validation
├── scripts/                            # Executable scripts
│   ├── sync-events                     # Main sync script (no extension)
│   ├── serve-gallery                   # Gallery server script
│   ├── setup-environment              # Environment setup
│   └── validate-system                # System validation
├── tools/                              # Development and debug tools
│   ├── debug/
│   │   ├── local-runner.sh             # Local GitHub Actions simulation
│   │   ├── connectivity-test.sh        # Connection testing
│   │   └── github-diagnostics.py       # GitHub Actions debugging
│   ├── migration/
│   │   ├── consolidate-scripts.py      # Script consolidation tool
│   │   └── cleanup-old-files.py        # Cleanup automation
│   └── monitoring/
│       ├── duplicate-monitor.py        # Duplicate detection
│       └── venue-validator.py          # Venue validation checker
├── docs/                               # Documentation
│   ├── README.md                       # Documentation index
│   ├── setup/                          # Setup and deployment guides
│   ├── api/                            # API documentation
│   ├── troubleshooting/                # Troubleshooting guides
│   └── development/                    # Development guides
├── tests/                              # Test suite
│   ├── __init__.py
│   ├── test_scrapers.py
│   ├── test_sync.py
│   ├── test_deduplication.py
│   └── fixtures/                       # Test data
├── config/                             # Configuration files
│   ├── production.env.example
│   ├── development.env.example
│   └── github-actions.env.example
├── deployment/                         # Deployment configurations
│   ├── ansible/                        # Ansible playbooks (moved from root)
│   ├── docker/                         # Docker configurations
│   └── systemd/                        # Service files
└── archive/                           # Archived/legacy files
    ├── old-scripts/                    # Archived scripts
    ├── old-workflows/                  # Archived workflows
    └── migration-notes.md              # Migration documentation
```

## 📋 **Script Consolidation Plan**

### **Core Production Scripts** (Keep and Refactor)
1. `automated_sync_working_fixed_with_venue_enforcement.py` → `src/sync/main.py`
2. `serve_flyers_enhanced.py` → `src/gallery/server.py`
3. `robust_deduplication_system.py` → `src/sync/deduplication.py`
4. `venue_assignment_fixer.py` → `src/sync/venue_validation.py`

### **Scrapers** (Consolidate)
- Keep: `conduit_scraper.py`, `willspub_scraper_enhanced.py`, `songkick_scraper_fixed.py`
- Archive: 8+ other scraper variants

### **Debug Tools** (Consolidate to 3)
1. `local_debug_runner.sh` → `tools/debug/local-runner.sh`
2. `advanced_github_actions_debug.py` → `tools/debug/github-diagnostics.py`
3. `quick_connectivity_test.sh` → `tools/debug/connectivity-test.sh`

### **Monitoring** (Consolidate)
1. `comprehensive_monitoring_system.py` → `tools/monitoring/system-monitor.py`
2. `duplicate_monitoring.py` → `tools/monitoring/duplicate-monitor.py`

### **Archive** (90+ scripts)
- All `*_backup.py` files
- All `*_old.py` files
- All intermediate debugging scripts
- All test/experimental scripts

## 🚀 **Quick Wins Implementation Plan**

### **Phase 1: Immediate Cleanup (Day 1)**
1. Archive virtual environment directory
2. Archive backup and old scripts
3. Consolidate GitHub Actions workflows
4. Update .gitignore

### **Phase 2: Core Restructuring (Days 2-3)**
1. Create new directory structure
2. Move and rename core production scripts
3. Set up proper Python package structure
4. Create consolidated entry point scripts

### **Phase 3: Code Quality (Days 4-5)**
1. Set up automated formatting (Black, isort)
2. Add linting (flake8, shellcheck)
3. Standardize docstrings and comments
4. Add type hints to core functions

### **Phase 4: Testing & Validation (Day 6)**
1. Create basic test suite
2. Validate all core functionality works
3. Test GitHub Actions workflows
4. Update documentation

## ⚙️ **Automation Tools Needed**

1. **pyproject.toml** - Python project configuration
2. **pre-commit hooks** - Automated code quality
3. **Makefile** - Common development tasks
4. **Migration scripts** - Automated file reorganization
5. **requirements.txt** - Dependency management

## 📊 **Expected Outcomes**

- **90% reduction** in script count (120+ → 12 core scripts)
- **75% reduction** in workflow files (15 → 4)  
- **Clear separation** of production vs development code
- **Standardized** code formatting and documentation
- **Improved maintainability** and developer onboarding
- **Automated quality checks** via pre-commit hooks

## 🔧 **Tools & Technologies**

- **Black** - Python code formatting
- **isort** - Import sorting
- **flake8** - Python linting
- **shellcheck** - Shell script linting
- **pre-commit** - Git hooks for quality checks
- **pytest** - Testing framework
- **mypy** - Type checking (future enhancement)

