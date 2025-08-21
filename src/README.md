# Orlando Punx Infrastructure - Source Code

This directory contains the core refactored source code organized as a proper Python package.

## Structure

- **scrapers/** - Event data scrapers (Will's Pub, Conduit, etc.)
- **sync/** - Gancio synchronization and deduplication logic
- **gallery/** - Flyer gallery server components  
- **utils/** - Shared utilities and configuration management

## Usage

This is the new structure being gradually migrated from `scripts/event-sync/`.
Production code currently still runs from the original location until migration is complete.

## Migration Status

- [ ] Scrapers migrated
- [ ] Sync logic migrated  
- [ ] Gallery server migrated
- [ ] Utils migrated
- [ ] Tests created
- [ ] Workflows updated

