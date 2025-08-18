#!/bin/bash

# SEO Deployment Script for Orlando Punk Shows
# This script deploys SEO improvements to the Gancio installation

set -e

echo "🎸 Deploying SEO improvements for Orlando Punk Shows..."

# Backup current configuration
echo "📋 Creating backup of current nuxt.config.js..."
sudo cp /usr/lib/node_modules/gancio/nuxt.config.js /usr/lib/node_modules/gancio/nuxt.config.js.backup-$(date +%Y%m%d_%H%M%S)

# Deploy improved nuxt.config.js
echo "🔧 Deploying enhanced nuxt.config.js..."
sudo cp seo-improvements/nuxt.config.js /usr/lib/node_modules/gancio/nuxt.config.js

# Deploy sitemap.xml
echo "🗺️  Deploying sitemap.xml..."
sudo cp seo-improvements/sitemap.xml /usr/lib/node_modules/gancio/static/sitemap.xml

# Deploy robots.txt
echo "🤖 Deploying robots.txt..."
sudo cp seo-improvements/robots.txt /usr/lib/node_modules/gancio/static/robots.txt

# Create Google Analytics integration file (placeholder)
echo "📊 Creating Google Analytics placeholder..."
sudo tee /usr/lib/node_modules/gancio/static/analytics.js > /dev/null << 'ANALYTICS'
// Google Analytics 4 Integration for Orlando Punk Shows
// Replace GA_MEASUREMENT_ID with your actual Google Analytics 4 Measurement ID

(function() {
  // Check if GA_MEASUREMENT_ID is set (replace this with actual ID)
  var GA_MEASUREMENT_ID = 'G-XXXXXXXXXX'; // Replace with your GA4 ID
  
  if (GA_MEASUREMENT_ID !== 'G-XXXXXXXXXX') {
    // Load Google Analytics
    var script = document.createElement('script');
    script.async = true;
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_MEASUREMENT_ID;
    document.head.appendChild(script);
    
    window.dataLayer = window.dataLayer || [];
    function gtag(){dataLayer.push(arguments);}
    gtag('js', new Date());
    gtag('config', GA_MEASUREMENT_ID, {
      page_title: document.title,
      custom_map: {
        'custom_parameter_1': 'punk_shows',
        'custom_parameter_2': 'orlando'
      }
    });
    
    console.log('📊 Google Analytics loaded for Orlando Punk Shows');
  } else {
    console.log('📊 Google Analytics not configured - update GA_MEASUREMENT_ID in analytics.js');
  }
})();
ANALYTICS

# Set proper permissions
sudo chown root:root /usr/lib/node_modules/gancio/nuxt.config.js
sudo chown root:root /usr/lib/node_modules/gancio/static/sitemap.xml
sudo chown root:root /usr/lib/node_modules/gancio/static/robots.txt
sudo chown root:root /usr/lib/node_modules/gancio/static/analytics.js

echo "✅ SEO improvements deployed successfully!"
echo ""
echo "🚀 Next steps:"
echo "1. Restart Gancio service: sudo systemctl restart gancio"
echo "2. Set up Google Analytics 4 and update analytics.js with your measurement ID"
echo "3. Set up Google Search Console and submit sitemap"
echo "4. Test the changes at https://orlandopunx.com"
echo ""
echo "🎯 SEO improvements include:"
echo "   ✓ Fixed language from Italian to English (lang='en-US')"
echo "   ✓ Enhanced meta tags with Orlando punk keywords"
echo "   ✓ Comprehensive Open Graph and Twitter Card tags"
echo "   ✓ JSON-LD structured data for better search understanding"
echo "   ✓ Local SEO optimization for Orlando, FL"
echo "   ✓ Sitemap.xml for better search engine indexing"
echo "   ✓ Updated robots.txt with sitemap reference"
echo "   ✓ Google Analytics integration ready"
echo ""
echo "🔍 Monitor your progress:"
echo "   • Google Search Console: https://search.google.com/search-console"
echo "   • Google Analytics: https://analytics.google.com"
echo "   • Test structured data: https://search.google.com/test/rich-results"
echo ""

