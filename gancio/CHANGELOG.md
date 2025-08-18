# Changelog

All notable changes to the OrlandoPunx.com Gancio customizations will be documented in this file.

## [1.0.0] - 2025-08-18

### Added
- Initial repository setup with Git version control
- Custom CSS for image display improvements
- Configuration templates with sensitive data sanitized
- Integration scripts for WillsPub event synchronization
- Deployment automation script
- Comprehensive documentation

### Changed
- **Image Display**: Modified event images to show complete flyers instead of cropped squares
  - Changed `object-fit` from `cover` to `contain`
  - Removed forced aspect ratios
  - Enhanced image container flexibility
- **Layout**: Improved event grid presentation while maintaining responsive design

### Fixed
- Event flyers now display completely, matching the clean presentation style of hattiesburg.askapunk.net
- CSS specificity issues that were preventing custom styles from applying properly

### Technical Details
- Repository structure organized with proper separation of concerns
- Sensitive configuration data excluded via comprehensive .gitignore
- Automated deployment script for easy application of customizations
- Service configuration files included for complete system setup

### Breaking Changes
- None (first release)

### Migration Notes
- To apply these customizations to an existing Gancio installation, use the deployment script
- Always backup existing configuration before applying changes
