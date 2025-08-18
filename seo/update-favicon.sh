#!/bin/bash

# Update OrlandoPunx.com to use the new poster favicon

echo "🎨 Updating OrlandoPunx.com favicon..."

# Copy the favicon to Gancio static directory
sudo cp icons8-poster-64.png /usr/lib/node_modules/gancio/static/favicon.png
sudo cp icons8-poster-64.png /usr/lib/node_modules/gancio/static/favicon.ico

# Set proper permissions
sudo chown root:root /usr/lib/node_modules/gancio/static/favicon.png
sudo chown root:root /usr/lib/node_modules/gancio/static/favicon.ico

echo "✅ Favicon updated successfully!"
echo ""
echo "The poster icon is now available at:"
echo "   • https://orlandopunx.com/favicon.png"
echo "   • https://orlandopunx.com/favicon.ico"
echo ""
echo "🔄 Consider updating nuxt.config.js to reference the new favicon:"
echo "   { rel: 'icon', type: 'image/png', href: '/favicon.png' }"
echo "   { rel: 'apple-touch-icon', href: '/favicon.png' }"
echo ""
echo "This poster icon is perfect for the punk show theme! 🎸"
