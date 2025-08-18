# Gancio Customizations for OrlandoPunx.com

This repository contains all customizations and configuration files for the Gancio installation at orlandopunx.com.

## Overview

Gancio is a shared agenda platform for local communities. This repository tracks our custom styling, configuration, and integration scripts.

## Directory Structure

```
├── assets/           # Custom CSS and static assets
├── config/           # Configuration files and templates
├── scripts/          # Integration and utility scripts
├── backup/           # Backup and restore scripts
└── README.md         # This file
```

## Key Customizations

### Custom Styling (`assets/custom-style.css`)
- **Image Display Fix**: Modified image handling to show complete event flyers instead of cropped squares
- **Layout Adjustments**: Customized the event grid layout for better visual presentation
- **Color Scheme**: Maintained the existing color palette while improving readability

Key CSS changes:
- `object-fit: contain` instead of `cover` for full flyer visibility
- Removed forced aspect ratios that were cropping images
- Enhanced image container flexibility

### Configuration (`config/`)
- `config.json.example`: Template configuration with sensitive data removed
- `gancio.service`: Systemd service configuration

### Integration Scripts (`scripts/`)
- `willspub_to_gancio_final_working.py`: Script to sync events from WillsPub to Gancio
- `gancio_api_detective.py`: API exploration and testing utility

## Installation

### 1. Install Gancio
```bash
sudo npm install -g gancio
```

### 2. Apply Custom Styling
```bash
sudo cp assets/custom-style.css /usr/lib/node_modules/gancio/assets/style.css
sudo systemctl restart gancio
```

### 3. Configure Gancio
1. Copy `config/config.json.example` to `/var/lib/gancio/config.json`
2. Update configuration with your specific settings:
   - Database credentials
   - SMTP settings
   - Base URL and hostname

### 4. Set up Service
```bash
sudo cp config/gancio.service /etc/systemd/system/
sudo systemctl enable gancio
sudo systemctl start gancio
```

## Maintenance

### Backup
- Database backups are handled by the system backup scripts in `/opt/backups/gancio/`
- Configuration backups should be created before major changes
- Always test changes in a staging environment first

### Updates
1. Before updating Gancio, backup current customizations
2. Update Gancio: `sudo npm update -g gancio`
3. Reapply custom CSS and configuration
4. Test thoroughly

### Monitoring
- Service status: `systemctl status gancio`
- Logs: `journalctl -u gancio -f`
- Gancio logs: `/var/lib/gancio/logs/`

## Troubleshooting

### Service Won't Start
- Check logs: `sudo journalctl -u gancio -n 50`
- Verify configuration file syntax
- Ensure all dependencies are installed

### Custom CSS Not Applied
- Verify file permissions on style.css
- Clear browser cache
- Restart Gancio service after CSS changes

### Image Display Issues
- Verify the custom CSS overrides are present
- Check browser developer tools for CSS conflicts
- Ensure images are properly uploaded to Gancio

## Contributing

When making changes:

1. Create a new branch: `git checkout -b feature/description`
2. Make changes and test thoroughly
3. Update this README if needed
4. Commit with descriptive messages
5. Push and create a pull request

## Contact

For questions about this setup, contact the system administrator.

## License

This configuration is specific to orlandopunx.com. Use at your own risk.

## Repository Setup

### To connect to a remote repository (GitHub example):

1. Create a new repository on GitHub (or your preferred Git host)
2. Add the remote:
   ```bash
   git remote add origin https://github.com/yourusername/gancio-customizations.git
   ```
3. Push the initial commit:
   ```bash
   git branch -M main
   git push -u origin main
   ```

### For private repositories:
If this repository contains any sensitive configuration data, make sure to:
- Set the repository as private
- Review all files before pushing
- Use the provided .gitignore to exclude sensitive files

