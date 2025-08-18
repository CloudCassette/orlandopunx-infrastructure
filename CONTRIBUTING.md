# Contributing to Orlando Punk Shows Infrastructure

Thanks for your interest in improving the Orlando punk scene's digital presence! This guide will help you contribute effectively.

## 🎯 Getting Started

### Prerequisites
- Basic understanding of web technologies (HTML, CSS, JavaScript)
- Familiarity with Linux system administration
- Knowledge of Git version control
- Understanding of the Orlando punk scene (helpful but not required)

### Development Environment
```bash
# Clone the repository
git clone https://github.com/yourusername/orlandopunx-infrastructure.git
cd orlandopunx-infrastructure

# Review the current setup
cat README.md
ls -la docs/
```

## 🛠️ Areas for Contribution

### 1. SEO Improvements
- **Location**: `seo/`
- **Skills**: SEO, content optimization, analytics
- **Examples**: Keyword research, meta tag optimization, structured data

### 2. Visual Customizations
- **Location**: `gancio/themes/`
- **Skills**: CSS, responsive design, UX/UI
- **Examples**: Mobile improvements, accessibility enhancements

### 3. Event Integration
- **Location**: `scripts/event-sync/`
- **Skills**: Python, web scraping, APIs
- **Examples**: New venue integrations, data quality improvements

### 4. System Monitoring
- **Location**: `monitoring/`
- **Skills**: Bash scripting, system administration
- **Examples**: Performance monitoring, alerting improvements

### 5. Documentation
- **Location**: `docs/`
- **Skills**: Technical writing, documentation
- **Examples**: Setup guides, troubleshooting, API docs

## 🚀 Contribution Process

### 1. Fork and Branch
```bash
# Fork the repository on GitHub, then:
git clone https://github.com/your-username/orlandopunx-infrastructure.git
cd orlandopunx-infrastructure

# Create feature branch
git checkout -b feature/your-improvement-name
```

### 2. Make Changes
- Follow existing code style and patterns
- Test changes thoroughly before submitting
- Update documentation as needed
- Consider backward compatibility

### 3. Testing Guidelines

#### For SEO Changes
```bash
# Test sitemap validity
curl https://orlandopunx.com/sitemap.xml
xmllint --noout --valid sitemap.xml

# Test robots.txt
curl https://orlandopunx.com/robots.txt

# Validate structured data
# Use Google's Rich Results Test
```

#### For System Changes
```bash
# Test service restart
sudo systemctl restart gancio
sudo systemctl status gancio

# Check website accessibility
curl -I https://orlandopunx.com

# Verify no broken functionality
./monitoring/health-check.sh
```

#### For CSS/Visual Changes
- Test on multiple screen sizes
- Verify accessibility compliance
- Check browser compatibility
- Ensure images display correctly

### 4. Commit Guidelines
```bash
# Use descriptive commit messages
git commit -m "🎨 Improve mobile event card layout

- Fix image aspect ratio on small screens
- Improve touch targets for better usability
- Add hover states for desktop users"

# Use emoji prefixes for commit types:
# 🎨 Visual improvements
# ⚡ Performance improvements
# 🐛 Bug fixes
# 📚 Documentation
# 🚀 New features
# 🔧 Configuration changes
# 🧪 Testing
# 🏗️ Infrastructure
```

### 5. Pull Request Process
1. **Create descriptive PR title and description**
2. **Include screenshots for visual changes**
3. **List all changes and rationale**
4. **Tag relevant maintainers**
5. **Wait for review and address feedback**

## 📋 Code Style Guidelines

### Shell Scripts
```bash
#!/bin/bash
# Always include error handling
set -e

# Use descriptive variable names
BACKUP_DIR="/opt/backups"
CURRENT_DATE=$(date +%Y%m%d)

# Include logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}
```

### CSS/Styling
```css
/* Use clear, semantic class names */
.event-card {
  /* Group related properties */
  display: flex;
  flex-direction: column;
  
  /* Responsive design first */
  width: 100%;
  max-width: 400px;
  
  /* Visual styling */
  background: var(--card-bg);
  border-radius: 8px;
}

/* Comment complex or punk-scene specific styles */
.punk-flyer-aspect {
  /* Maintain typical punk flyer proportions */
  aspect-ratio: 3/4;
}
```

### Documentation
- Use clear headings and structure
- Include code examples
- Provide context for Orlando-specific references
- Keep language accessible to newcomers

## 🎵 Orlando Punk Scene Context

### Understanding the Scene
- **Primary venues**: Will's Pub, Uncle Lou's
- **Typical events**: DIY shows, touring acts, local bands
- **Community values**: Accessibility, authenticity, inclusivity
- **Visual aesthetic**: Raw, authentic, high-contrast flyers

### Content Guidelines
- Respect the DIY ethos
- Prioritize functionality over flashiness
- Consider the community's diverse technical skills
- Maintain authentic punk aesthetic

## 🔍 Review Process

### What Reviewers Look For
1. **Functionality**: Does it work without breaking existing features?
2. **Performance**: Does it impact site speed or server resources?
3. **Security**: Are there any security implications?
4. **User Experience**: Does it improve the experience for punk show attendees?
5. **Maintainability**: Is the code clear and documented?

### Response Time
- **Initial review**: Within 1-2 weeks
- **Follow-up reviews**: 3-5 business days
- **Emergency fixes**: Same day (if critical)

## 🆘 Getting Help

### Resources
- **Documentation**: Check `docs/` directory first
- **API Reference**: `docs/API_DOCUMENTATION.md`
- **Setup Guide**: `docs/DEPLOYMENT_GUIDE.md`
- **Troubleshooting**: `docs/troubleshooting/`

### Communication
- **Issues**: GitHub issues for bugs and feature requests
- **Questions**: GitHub discussions for general questions
- **Urgent**: Email godlessamericarecords@gmail.com for emergencies

### Community Guidelines
- Be respectful and inclusive
- Focus on constructive feedback
- Remember we're all here to support the Orlando punk scene
- Help newcomers feel welcome

## 🏷️ Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or improvement
- `documentation`: Documentation improvements
- `seo`: SEO-related changes
- `performance`: Performance improvements
- `accessibility`: Accessibility improvements
- `punk-scene`: Orlando punk scene specific
- `good-first-issue`: Good for newcomers
- `help-wanted`: Extra attention needed

## 📈 Success Metrics

Contributions are successful when they:
- Increase event discovery and attendance
- Improve website performance or usability
- Strengthen the Orlando punk community connection
- Maintain or improve search engine rankings
- Reduce maintenance overhead

---

**🎸 Thanks for helping make the Orlando punk scene more discoverable! 🎸**

*Every contribution helps more people discover awesome local shows!*
