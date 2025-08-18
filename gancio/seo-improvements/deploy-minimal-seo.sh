#!/bin/bash

# Minimal SEO Deployment Script for Orlando Punk Shows
# This script adds basic SEO files without modifying the main configuration

set -e

echo "🎸 Deploying minimal SEO improvements for Orlando Punk Shows..."

# Deploy sitemap.xml (this should work fine)
echo "🗺️  Deploying sitemap.xml..."
sudo cp seo-improvements/sitemap.xml /usr/lib/node_modules/gancio/static/sitemap.xml

# Deploy robots.txt
echo "🤖 Deploying robots.txt..."
sudo cp seo-improvements/robots.txt /usr/lib/node_modules/gancio/static/robots.txt

# Create a simple SEO CSS file with some improvements
echo "📝 Creating SEO enhancement CSS..."
sudo tee /usr/lib/node_modules/gancio/static/seo-enhancements.css > /dev/null << 'CSS'
/* SEO Enhancement CSS for Orlando Punk Shows */

/* Improve text readability for better SEO */
body {
  font-size: 16px;
  line-height: 1.6;
}

/* Better heading hierarchy */
h1, h2, h3, h4, h5, h6 {
  font-weight: bold;
  margin: 1em 0 0.5em 0;
}

/* Improve image SEO */
img {
  max-width: 100%;
  height: auto;
}

/* Better link styling for accessibility */
a {
  text-decoration: underline;
}

a:hover, a:focus {
  text-decoration: none;
}

/* Print styles for better accessibility */
@media print {
  .v-navigation-drawer,
  .v-app-bar,
  .v-btn {
    display: none !important;
  }
}
CSS

# Create a JavaScript snippet for basic analytics (optional)
echo "📊 Creating analytics snippet..."
sudo tee /usr/lib/node_modules/gancio/static/seo-helpers.js > /dev/null << 'JS'
// SEO Helper Functions for Orlando Punk Shows

(function() {
  'use strict';
  
  // Add structured data for events dynamically
  function addEventStructuredData() {
    const events = document.querySelectorAll('.event');
    events.forEach(function(eventEl) {
      const title = eventEl.querySelector('.title');
      const date = eventEl.querySelector('time');
      const venue = eventEl.querySelector('.place');
      
      if (title && date && venue) {
        const structuredData = {
          '@context': 'https://schema.org',
          '@type': 'MusicEvent',
          'name': title.textContent.trim(),
          'startDate': date.getAttribute('datetime'),
          'location': {
            '@type': 'MusicVenue',
            'name': venue.textContent.trim(),
            'address': 'Orlando, FL'
          },
          'organizer': {
            '@type': 'Organization',
            'name': 'Orlando Punk Shows',
            'url': 'https://orlandopunx.com'
          }
        };
        
        const script = document.createElement('script');
        script.type = 'application/ld+json';
        script.textContent = JSON.stringify(structuredData);
        eventEl.appendChild(script);
      }
    });
  }
  
  // Improve meta descriptions dynamically
  function improveMetaDescription() {
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc && metaDesc.getAttribute('content').length < 50) {
      metaDesc.setAttribute('content', 
        'Discover underground punk shows, hardcore concerts, and indie music events in Orlando, Florida. Find upcoming shows at Will\'s Pub, Uncle Lou\'s, and other local venues.'
      );
    }
  }
  
  // Add missing alt text to images
  function addImageAltText() {
    const images = document.querySelectorAll('img:not([alt])');
    images.forEach(function(img) {
      const eventTitle = img.closest('.event')?.querySelector('.title')?.textContent || '';
      if (eventTitle) {
        img.setAttribute('alt', eventTitle + ' - Orlando punk show flyer');
      } else {
        img.setAttribute('alt', 'Orlando punk show event flyer');
      }
    });
  }
  
  // Run improvements when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setTimeout(function() {
        addEventStructuredData();
        improveMetaDescription();
        addImageAltText();
      }, 1000);
    });
  } else {
    setTimeout(function() {
      addEventStructuredData();
      improveMetaDescription();
      addImageAltText();
    }, 1000);
  }
})();
JS

# Update the custom image fix CSS to reference our new SEO CSS
echo "🔧 Updating custom image fix CSS to include SEO enhancements..."
sudo tee -a /usr/lib/node_modules/gancio/static/custom-image-fix.css > /dev/null << 'APPEND'

/* Import SEO enhancements */
@import url('/seo-enhancements.css');
APPEND

# Set proper permissions
sudo chown root:root /usr/lib/node_modules/gancio/static/sitemap.xml
sudo chown root:root /usr/lib/node_modules/gancio/static/robots.txt
sudo chown root:root /usr/lib/node_modules/gancio/static/seo-enhancements.css
sudo chown root:root /usr/lib/node_modules/gancio/static/seo-helpers.js

echo "✅ Minimal SEO improvements deployed successfully!"
echo ""
echo "🚀 Changes include:"
echo "   ✓ sitemap.xml for search engines"
echo "   ✓ robots.txt with sitemap reference"  
echo "   ✓ SEO enhancement CSS for better readability"
echo "   ✓ JavaScript helpers for dynamic structured data"
echo ""
echo "🔄 Restart Gancio to see changes: sudo systemctl restart gancio"
echo ""
echo "🎯 To add these files to the HTML, manually edit nuxt.config.js:"
echo "   Add to head.link: { rel: 'stylesheet', href: '/seo-enhancements.css' }"
echo "   Add to head.script: { src: '/seo-helpers.js', async: true, body: true }"
echo ""

