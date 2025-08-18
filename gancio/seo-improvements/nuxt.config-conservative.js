const config = require('./server/config.js')
const minifyTheme = require('minify-css-string').default

const isDev = (process.env.NODE_ENV !== 'production')
module.exports = {
  telemetry: false,
  modern: (process.env.NODE_ENV === 'production') && 'client',
  /*
   ** Enhanced Headers for SEO - Conservative approach
   */
  head: {
    title: 'Orlando Punk Shows | Underground Music Events & Concert Calendar | Orlando, FL',
    titleTemplate: '%s | Orlando Punk Shows',
    meta: [
      { charset: 'utf-8' },
      { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      { 
        hid: 'description', 
        name: 'description', 
        content: 'Discover underground punk shows, hardcore concerts, and indie music events in Orlando, Florida. Find upcoming shows at Will\'s Pub, Uncle Lou\'s, and other local venues. Your guide to Orlando\'s punk scene.' 
      },
      { 
        hid: 'keywords', 
        name: 'keywords', 
        content: 'Orlando punk shows, Orlando hardcore concerts, Will\'s Pub events, Orlando underground music, punk shows Orlando FL, Orlando music calendar, DIY shows Orlando, punk rock Orlando' 
      },
      { name: 'author', content: 'Orlando Punk Shows' },
      { name: 'robots', content: 'index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1' },
      // Geographic Meta Tags for Local SEO
      { name: 'geo.region', content: 'US-FL' },
      { name: 'geo.placename', content: 'Orlando, Florida' },
      { name: 'geo.position', content: '28.5383;-81.3792' },
      { name: 'ICBM', content: '28.5383, -81.3792' },
      // Enhanced Open Graph - keeping existing structure
      { hid: 'og:title', property: 'og:title', content: 'Orlando Punk Shows | Underground Music Events & Concert Calendar' },
      { hid: 'og:description', property: 'og:description', content: 'Discover underground punk shows, hardcore concerts, and indie music events in Orlando, Florida. Find upcoming shows at Will\'s Pub, Uncle Lou\'s, and other local venues.' },
      { hid: 'og:url', property: 'og:url', content: 'https://orlandopunx.com' },
      { property: 'og:image', content: 'https://orlandopunx.com/logo.png' },
      { property: 'og:site_name', content: 'Orlando Punk Shows' },
      { property: 'og:type', content: 'website' },
      { property: 'og:locale', content: 'en_US' },
      // Twitter Card
      { name: 'twitter:card', content: 'summary_large_image' },
      { name: 'twitter:title', content: 'Orlando Punk Shows | Underground Music Events' },
      { name: 'twitter:description', content: 'Your guide to Orlando\'s punk scene - find underground shows, hardcore concerts, and indie music events.' },
      { name: 'twitter:image', content: 'https://orlandopunx.com/logo.png' }
    ],
    link: [
      { rel: 'icon', type: 'image/png', href: '/logo.png' }, 
      { rel: 'apple-touch-icon', href: '/logo.png' },
      { rel: 'stylesheet', href: '/custom-image-fix.css' },
      { rel: 'canonical', href: 'https://orlandopunx.com' },
      { rel: 'alternate', type: 'application/rss+xml', title: 'Orlando Punk Shows RSS Feed', href: '/feed/rss' }
    ],
    script: [
      { src: '/gancio-events.es.js', async: true, body: true },
      // JSON-LD Structured Data - simplified version
      {
        hid: 'ld-json-org',
        type: 'application/ld+json',
        innerHTML: JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'Organization',
          name: 'Orlando Punk Shows',
          url: 'https://orlandopunx.com',
          logo: 'https://orlandopunx.com/logo.png',
          description: 'Digital poster wall for underground punk shows in Orlando, FL',
          areaServed: {
            '@type': 'City',
            name: 'Orlando',
            addressRegion: 'FL',
            addressCountry: 'US'
          },
          sameAs: [
            'https://orlandopunx.com/feed/rss'
          ]
        })
      },
      {
        hid: 'ld-json-website',
        type: 'application/ld+json',
        innerHTML: JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'WebSite',
          name: 'Orlando Punk Shows',
          url: 'https://orlandopunx.com',
          description: 'Underground punk shows and events in Orlando, Florida',
          potentialAction: {
            '@type': 'SearchAction',
            target: {
              '@type': 'EntryPoint',
              urlTemplate: 'https://orlandopunx.com/?search={search_term_string}'
            },
            'query-input': 'required name=search_term_string'
          }
        })
      }
    ],
    __dangerouslyDisableSanitizersByTagID: {
      'ld-json-org': ['innerHTML'],
      'ld-json-website': ['innerHTML']
    }
  },
  dev: isDev,
  server: config.server,

  vue: {
    config: {
      ignoredElements: ['gancio-events', 'gancio-event']
    }
  },

  css: ['./assets/style.css']
}
