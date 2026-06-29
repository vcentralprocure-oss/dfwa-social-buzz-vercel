/**
 * DFWA Social Buzz - Runtime Schema Injection
 * 
 * Client-side script that injects JSON-LD schema into the page at runtime.
 * Only touches the <head> to add script tags - no DOM manipulation of content.
 * 
 * Usage: Include this script in your HTML <head>:
 * <script src="/lib/runtime-schema.js" data-article-id="article-slug"></script>
 */

(function() {
  'use strict';
  
  // Configuration
  const CONFIG = {
    siteName: "DFWA Social Buzz",
    siteUrl: "https://dfwasocialbuzz.com",
    logo: "https://dfwasocialbuzz.com/logo.png",
    cities: {
      arlington: {
        name: "Arlington Pulse",
        url: "https://arlington.dfwasocialbuzz.com"
      }
    }
  };

  /**
   * Create and inject a JSON-LD script tag
   * @param {Object} schema - Schema object
   */
  function injectSchema(schema) {
    if (!schema || !schema['@type']) return;
    
    // Validate before injecting
    if (!schema['@context']) {
      schema['@context'] = 'https://schema.org';
    }
    
    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.textContent = JSON.stringify(schema, null, 2);
    
    document.head.appendChild(script);
  }

  /**
   * Get Organization schema
   */
  function getOrganizationSchema() {
    return {
      "@context": "https://schema.org",
      "@type": "NewsMediaOrganization",
      "@id": `${CONFIG.siteUrl}/#organization`,
      "name": CONFIG.siteName,
      "url": CONFIG.siteUrl,
      "logo": {
        "@type": "ImageObject",
        "url": CONFIG.logo,
        "width": 512,
        "height": 512
      },
      "sameAs": [
        "https://facebook.com/dfwasocialbuzz",
        "https://twitter.com/dfwasocialbuzz",
        "https://instagram.com/dfwasocialbuzz"
      ],
      "foundingDate": "2024"
    };
  }

  /**
   * Get Article schema from meta tags
   */
  function getArticleSchemaFromMeta() {
    const getMeta = (name) => {
      const tag = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
      return tag ? tag.content : null;
    };
    
    const headline = document.title.replace(/\|.*$/, '').trim();
    const description = getMeta('description') || getMeta('og:description');
    const url = window.location.href;
    const image = getMeta('og:image') || getMeta('twitter:image');
    const published = getMeta('article:published_time') || getMeta('published_date');
    const author = getMeta('author') || getMeta('article:author') || 'DFWA Social Buzz Staff';
    
    // Detect city from URL
    const cityMatch = url.match(/\/([a-z]+)\.dfwasocialbuzz\.com/);
    const cityKey = cityMatch ? cityMatch[1] : 'arlington';
    const city = CONFIG.cities[cityKey] || CONFIG.cities.arlington;
    
    const schema = {
      "@context": "https://schema.org",
      "@type": "NewsArticle",
      "@id": `${url}#article`,
      "headline": headline,
      "description": description,
      "url": url,
      "datePublished": published || new Date().toISOString(),
      "author": {
        "@type": "Person",
        "name": author
      },
      "publisher": {
        "@id": `${CONFIG.siteUrl}/#organization`
      },
      "isPartOf": {
        "@type": "WebPage",
        "@id": `${city.url}/#webpage`
      },
      "articleSection": city.name,
      "inLanguage": "en-US"
    };
    
    if (image) {
      schema.image = {
        "@type": "ImageObject",
        "url": image,
        "width": 1200,
        "height": 630
      };
    }
    
    return schema;
  }

  /**
   * Initialize schema injection
   */
  function init() {
    // Always inject Organization schema
    injectSchema(getOrganizationSchema());
    
    // Detect page type and inject appropriate schema
    const isArticle = document.querySelector('article') || 
                      document.querySelector('[data-article]') ||
                      document.querySelector('meta[property="og:type"][content="article"]');
    
    if (isArticle) {
      injectSchema(getArticleSchemaFromMeta());
    }
    
    // Log in development
    if (window.location.hostname === 'localhost' || window.location.search.includes('debug=1')) {
      console.log('[DFWA Schema] Injected schemas for:', isArticle ? 'article' : 'page');
    }
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
