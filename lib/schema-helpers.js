/**
 * DFWA Social Buzz - Schema Helper Functions
 * Centralized JSON-LD schema generation for templates
 * 
 * Usage: Import these helpers in your build process or serverless functions
 * to generate schema objects that get stringified into <script> tags.
 */

const SITE_CONFIG = {
  name: "DFWA Social Buzz",
  url: "https://dfwasocialbuzz.com",
  logo: "https://dfwasocialbuzz.com/logo.png",
  description: "Your source for local news, events, and community updates across the Dallas-Fort Worth-Arlington metroplex.",
  sameAs: [
    "https://facebook.com/dfwasocialbuzz",
    "https://twitter.com/dfwasocialbuzz",
    "https://instagram.com/dfwasocialbuzz"
  ],
  foundingDate: "2024",
  address: {
    locality: "Dallas-Fort Worth",
    region: "TX",
    country: "US"
  }
};

const CITY_CONFIG = {
  arlington: {
    name: "Arlington Pulse",
    slug: "arlington",
    url: "https://arlington.dfwasocialbuzz.com",
    description: "Local news and events for Arlington, Texas",
    areaServed: {
      city: "Arlington",
      state: "Texas"
    }
  },
  dallas: {
    name: "Dallas Current",
    slug: "dallas",
    url: "https://dallas.dfwasocialbuzz.com",
    description: "Local news and events for Dallas, Texas",
    areaServed: {
      city: "Dallas",
      state: "Texas"
    }
  },
  fortworth: {
    name: "Fort Worth Eco",
    slug: "fortworth",
    url: "https://fortworth.dfwasocialbuzz.com",
    description: "Local news and events for Fort Worth, Texas",
    areaServed: {
      city: "Fort Worth",
      state: "Texas"
    }
  }
};

/**
 * Get NewsMediaOrganization schema
 * @returns {Object} Organization schema object
 */
function getOrganizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "NewsMediaOrganization",
    "@id": `${SITE_CONFIG.url}/#organization`,
    "name": SITE_CONFIG.name,
    "url": SITE_CONFIG.url,
    "logo": {
      "@type": "ImageObject",
      "url": SITE_CONFIG.logo,
      "width": 512,
      "height": 512
    },
    "description": SITE_CONFIG.description,
    "sameAs": SITE_CONFIG.sameAs,
    "foundingDate": SITE_CONFIG.foundingDate,
    "address": {
      "@type": "PostalAddress",
      "addressLocality": SITE_CONFIG.address.locality,
      "addressRegion": SITE_CONFIG.address.region,
      "addressCountry": SITE_CONFIG.address.country
    }
  };
}

/**
 * Get WebSite schema
 * @returns {Object} WebSite schema object
 */
function getWebSiteSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "@id": `${SITE_CONFIG.url}/#website`,
    "name": SITE_CONFIG.name,
    "url": SITE_CONFIG.url,
    "publisher": {
      "@id": `${SITE_CONFIG.url}/#organization`
    },
    "potentialAction": {
      "@type": "SearchAction",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": `${SITE_CONFIG.url}/search?q={search_term_string}`
      },
      "query-input": "required name=search_term_string"
    }
  };
}

/**
 * Get WebPage schema for city sections
 * @param {string} cityKey - City key (arlington, dallas, fortworth)
 * @param {Object} options - Optional overrides
 * @returns {Object|null} WebPage schema object
 */
function getWebPageSchema(cityKey, options = {}) {
  const city = CITY_CONFIG[cityKey];
  if (!city) return null;

  return {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "@id": `${city.url}/#webpage`,
    "url": options.url || city.url,
    "name": options.title || city.name,
    "description": options.description || city.description,
    "isPartOf": {
      "@id": `${SITE_CONFIG.url}/#website`
    },
    "about": {
      "@type": "City",
      "name": city.areaServed.city,
      "containedInPlace": {
        "@type": "State",
        "name": city.areaServed.state
      }
    },
    "publisher": {
      "@id": `${SITE_CONFIG.url}/#organization`
    }
  };
}

/**
 * Get NewsArticle schema
 * @param {Object} article - Article data
 * @returns {Object} NewsArticle schema object
 */
function getArticleSchema(article) {
  const {
    headline,
    description,
    url,
    image,
    datePublished,
    dateModified,
    author = "DFWA Social Buzz Staff",
    cityKey = "arlington",
    section = null
  } = article;

  const city = CITY_CONFIG[cityKey] || CITY_CONFIG.arlington;

  const schema = {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "@id": `${url}#article`,
    "headline": headline,
    "description": description,
    "url": url,
    "datePublished": datePublished,
    "dateModified": dateModified || datePublished,
    "author": {
      "@type": "Person",
      "name": author
    },
    "publisher": {
      "@id": `${SITE_CONFIG.url}/#organization`
    },
    "isPartOf": {
      "@type": "WebPage",
      "@id": `${city.url}/#webpage`
    },
    "articleSection": section || city.name,
    "inLanguage": "en-US",
    "mainEntityOfPage": {
      "@type": "WebPage",
      "@id": url
    }
  };

  // Only add image if provided
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
 * Get BreadcrumbList schema
 * @param {Array} items - Array of {name, url} objects
 * @returns {Object} BreadcrumbList schema object
 */
function getBreadcrumbSchema(items) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": items.map((item, index) => ({
      "@type": "ListItem",
      "position": index + 1,
      "name": item.name,
      "item": item.url
    }))
  };
}

/**
 * Get LocalBusiness schema
 * @param {Object} business - Business data
 * @returns {Object} LocalBusiness schema object
 */
function getLocalBusinessSchema(business) {
  const {
    name,
    description,
    url,
    telephone,
    address,
    image,
    cityKey = "arlington"
  } = business;

  const city = CITY_CONFIG[cityKey] || CITY_CONFIG.arlington;

  const schema = {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": name,
    "description": description,
    "url": url,
    "address": {
      "@type": "PostalAddress",
      "streetAddress": address.street,
      "addressLocality": address.city,
      "addressRegion": address.state || "TX",
      "postalCode": address.zip,
      "addressCountry": "US"
    },
    "areaServed": {
      "@type": "City",
      "name": city.areaServed.city
    }
  };

  if (telephone) schema.telephone = telephone;
  if (image) schema.image = image;

  return schema;
}

/**
 * Get all schemas for a page type
 * @param {string} pageType - Type of page (homepage, city-home, article, business)
 * @param {Object} data - Page-specific data
 * @returns {Array} Array of schema objects
 */
function getPageSchemas(pageType, data = {}) {
  const schemas = [];

  switch (pageType) {
    case "homepage":
      schemas.push(getOrganizationSchema());
      schemas.push(getWebSiteSchema());
      break;

    case "city-home":
      schemas.push(getOrganizationSchema());
      schemas.push(getWebSiteSchema());
      const webPage = getWebPageSchema(data.cityKey, {
        title: data.title,
        description: data.description,
        url: data.url
      });
      if (webPage) schemas.push(webPage);
      
      if (data.breadcrumbs) {
        schemas.push(getBreadcrumbSchema(data.breadcrumbs));
      }
      break;

    case "article":
      schemas.push(getOrganizationSchema());
      schemas.push(getArticleSchema(data));
      
      if (data.breadcrumbs) {
        schemas.push(getBreadcrumbSchema(data.breadcrumbs));
      }
      break;

    case "business":
      schemas.push(getOrganizationSchema());
      schemas.push(getLocalBusinessSchema(data));
      break;

    default:
      schemas.push(getOrganizationSchema());
      schemas.push(getWebSiteSchema());
  }

  return schemas.filter(Boolean); // Remove nulls
}

/**
 * Render schema objects as HTML script tags
 * @param {Array|Object} schemas - Schema object(s)
 * @returns {string} HTML string with script tags
 */
function renderSchemaScripts(schemas) {
  const schemaArray = Array.isArray(schemas) ? schemas : [schemas];
  
  return schemaArray
    .map(schema => {
      if (!schema) return '';
      const json = JSON.stringify(schema, null, 2);
      return `<script type="application/ld+json">\n${json}\n</script>`;
    })
    .filter(Boolean)
    .join('\n');
}

/**
 * Validate schema object (basic checks)
 * @param {Object} schema - Schema object to validate
 * @returns {Object} Validation result {valid: boolean, errors: string[]}
 */
function validateSchema(schema) {
  const errors = [];

  if (!schema) {
    errors.push('Schema is null or undefined');
    return { valid: false, errors };
  }

  if (!schema['@context']) {
    errors.push('Missing @context');
  } else if (schema['@context'] !== 'https://schema.org') {
    errors.push('@context should be "https://schema.org"');
  }

  if (!schema['@type']) {
    errors.push('Missing @type');
  }

  // Type-specific validation
  switch (schema['@type']) {
    case 'NewsArticle':
      if (!schema.headline) errors.push('NewsArticle missing headline');
      if (!schema.url) errors.push('NewsArticle missing url');
      if (!schema.datePublished) errors.push('NewsArticle missing datePublished');
      break;
    
    case 'NewsMediaOrganization':
      if (!schema.name) errors.push('Organization missing name');
      if (!schema.url) errors.push('Organization missing url');
      break;
    
    case 'WebSite':
      if (!schema.name) errors.push('WebSite missing name');
      if (!schema.url) errors.push('WebSite missing url');
      break;
  }

  return {
    valid: errors.length === 0,
    errors
  };
}

// Export for Node.js/CommonJS
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    // Config
    SITE_CONFIG,
    CITY_CONFIG,
    
    // Schema generators
    getOrganizationSchema,
    getWebSiteSchema,
    getWebPageSchema,
    getArticleSchema,
    getBreadcrumbSchema,
    getLocalBusinessSchema,
    getPageSchemas,
    
    // Utilities
    renderSchemaScripts,
    validateSchema
  };
}

// Export for ES modules
if (typeof exports !== 'undefined') {
  exports.SITE_CONFIG = SITE_CONFIG;
  exports.CITY_CONFIG = CITY_CONFIG;
  exports.getOrganizationSchema = getOrganizationSchema;
  exports.getWebSiteSchema = getWebSiteSchema;
  exports.getWebPageSchema = getWebPageSchema;
  exports.getArticleSchema = getArticleSchema;
  exports.getBreadcrumbSchema = getBreadcrumbSchema;
  exports.getLocalBusinessSchema = getLocalBusinessSchema;
  exports.getPageSchemas = getPageSchemas;
  exports.renderSchemaScripts = renderSchemaScripts;
  exports.validateSchema = validateSchema;
}
