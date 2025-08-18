const config = require('./server/config.js')
const minifyTheme = require('minify-css-string').default

const isDev = (process.env.NODE_ENV !== 'production')
module.exports = {
  telemetry: false,
  modern: (process.env.NODE_ENV === 'production') && 'client',
  /*
   ** Enhanced Headers for SEO
   */
  head: {
    htmlAttrs: {
      lang: 'en-US'  // Fixed: Changed from 'it' to 'en-US'
    },
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
      { name: 'language', content: 'en-US' },
      { name: 'revisit-after', content: '1 day' },
      { name: 'distribution', content: 'global' },
      { name: 'rating', content: 'general' },
      // Geographic Meta Tags for Local SEO
      { name: 'geo.region', content: 'US-FL' },
      { name: 'geo.placename', content: 'Orlando, Florida' },
      { name: 'geo.position', content: '28.5383;-81.3792' },
      { name: 'ICBM', content: '28.5383, -81.3792' },
      // Enhanced Open Graph
      { hid: 'og:type', property: 'og:type', content: 'website' },
      { hid: 'og:site_name', property: 'og:site_name', content: 'Orlando Punk Shows' },
      { hid: 'og:title', property: 'og:title', content: 'Orlando Punk Shows | Underground Music Events & Concert Calendar' },
      { hid: 'og:description', property: 'og:description', content: 'Discover underground punk shows, hardcore concerts, and indie music events in Orlando, Florida. Find upcoming shows at Will\'s Pub, Uncle Lou\'s, and other local venues.' },
      { hid: 'og:url', property: 'og:url', content: 'https://orlandopunx.com' },
      { hid: 'og:image', property: 'og:image', content: 'https://orlandopunx.com/logo.png' },
      { property: 'og:image:width', content: '1200' },
      { property: 'og:image:height', content: '630' },
      { property: 'og:locale', content: 'en_US' },
      // Twitter Card
      { name: 'twitter:card', content: 'summary_large_image' },
      { name: 'twitter:title', content: 'Orlando Punk Shows | Underground Music Events' },
      { name: 'twitter:description', content: 'Your guide to Orlando\'s punk scene - find underground shows, hardcore concerts, and indie music events.' },
      { name: 'twitter:image', content: 'https://orlandopunx.com/logo.png' },
      // Schema.org markup
      { itemprop: 'name', content: 'Orlando Punk Shows | Underground Music Events' },
      { itemprop: 'description', content: 'Discover underground punk shows, hardcore concerts, and indie music events in Orlando, Florida.' },
      { itemprop: 'image', content: 'https://orlandopunx.com/logo.png' }
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
      // JSON-LD Structured Data for Organization
      {
        hid: 'ld-json',
        type: 'application/ld+json',
        innerHTML: JSON.stringify({
          '@context': 'https://schema.org',
          '@graph': [
            {
              '@type': 'WebSite',
              '@id': 'https://orlandopunx.com/#website',
              url: 'https://orlandopunx.com',
              name: 'Orlando Punk Shows',
              description: 'Underground punk shows and events in Orlando, Florida',
              publisher: { '@id': 'https://orlandopunx.com/#organization' },
              potentialAction: [{
                '@type': 'SearchAction',
                target: {
                  '@type': 'EntryPoint',
                  urlTemplate: 'https://orlandopunx.com/?search={search_term_string}'
                },
                'query-input': 'required name=search_term_string'
              }],
              inLanguage: 'en-US'
            },
            {
              '@type': 'Organization',
              '@id': 'https://orlandopunx.com/#organization',
              name: 'Orlando Punk Shows',
              url: 'https://orlandopunx.com',
              logo: {
                '@type': 'ImageObject',
                inLanguage: 'en-US',
                '@id': 'https://orlandopunx.com/#/schema/logo',
                url: 'https://orlandopunx.com/logo.png',
                contentUrl: 'https://orlandopunx.com/logo.png',
                width: 512,
                height: 512
              },
              image: { '@id': 'https://orlandopunx.com/#/schema/logo' },
              description: 'Digital poster wall for underground punk shows in Orlando, FL',
              areaServed: {
                '@type': 'City',
                name: 'Orlando',
                addressRegion: 'FL',
                addressCountry: 'US'
              },
              knowsAbout: [
                'Punk Rock',
                'Hardcore Punk',
                'Underground Music',
                'Live Music Events',
                'Concert Promotion',
                'Orlando Music Scene'
              ]
            },
            {
              '@type': 'LocalBusiness',
              '@id': 'https://orlandopunx.com/#localbusiness',
              name: 'Orlando Punk Shows',
              description: 'Digital poster wall and event calendar for underground punk shows in Orlando, Florida',
              url: 'https://orlandopunx.com',
              address: {
                '@type': 'PostalAddress',
                addressLocality: 'Orlando',
                addressRegion: 'FL',
                addressCountry: 'US'
              },
              geo: {
                '@type': 'GeoCoordinates',
                latitude: '28.5383',
                longitude: '-81.3792'
              },
              openingHours: 'Mo-Su 00:00-23:59',
              serviceArea: {
                '@type': 'GeoCircle',
                geoMidpoint: {
                  '@type': 'GeoCoordinates',
                  latitude: '28.5383',
                  longitude: '-81.3792'
                },
                geoRadius: '50000'
              },
              areaServed: ['Orlando', 'Central Florida', 'Orange County'],
              knowsAbout: [
                'Punk Rock Events',
                'Hardcore Shows', 
                'Underground Music',
                'Live Concerts',
                'Orlando Music Scene'
              ]
            }
          ]
        })
      }
    ],
    __dangerouslyDisableSanitizersByTagID: {
      'ld-json': ['innerHTML']
    }
  },
  dev: isDev,
  server: config.server,

  vue: {
    config: {
      ignoredElements: ['gancio-events', 'gancio-event']
    }
  },

  css: ['./assets/style.css'],
  
  // Enhanced for better SEO
  render: {
    resourceHints: false  // Better control over resource hints
  },
  
  // Sitemap generation (if @nuxtjs/sitemap is available)
  sitemap: {
    hostname: 'https://orlandopunx.com',
    gzip: true,
    exclude: [
      '/admin/**',
      '/login',
      '/add'
    ]
  },

  // Better compression and caching
  build: {
    html: {
      minify: {
        collapseBooleanAttributes: true,
        decodeEntities: true,
        minifyCSS: true,
        minifyJS: true,
        processConditionalComments: true,
        removeEmptyAttributes: true,
        removeRedundantAttributes: true,
        trimCustomFragments: true,
        useShortDoctype: true,
        preserveLineBreaks: false,
        collapseWhitespace: true,
        removeComments: true
      }
    }
  },

  // Add robots.txt generation
  robotsTxt: {
    UserAgent: '*',
    Allow: '/',
    Sitemap: 'https://orlandopunx.com/sitemap.xml'
  }
}
