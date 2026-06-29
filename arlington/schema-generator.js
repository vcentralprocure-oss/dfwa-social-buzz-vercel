/**
 * DFWA Social Buzz - JSON-LD Schema Generator
 * Replicates AI Booster plugin functionality for static HTML
 */

const siteConfig = {
  name: "DFWA Social Buzz",
  url: "https://dfwasocialbuzz.com",
  logo: "https://dfwasocialbuzz.com/logo.png",
  description: "Your source for local news, events, and community updates across the Dallas-Fort Worth-Arlington metroplex.",
  sameAs: [
    "https://facebook.com/dfwasocialbuzz",
    "https://twitter.com/dfwasocialbuzz",
    "https://instagram.com/dfwasocialbuzz"
  ]
};

const cityConfig = {
  arlington: {
    name: "Arlington Pulse",
    url: "https://arlington.dfwasocialbuzz.com",
    description: "Local news and events for Arlington, Texas",
    areaServed: {
      "@type": "City",
      "name": "Arlington",
      "containedInPlace": {
        "@type": "State",
        "name": "Texas"
      }
    }
  }
};

/**
 * Generate NewsMediaOrganization schema
 */
function generateOrganizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "NewsMediaOrganization",
    "name": siteConfig.name,
    "url": siteConfig.url,
    "logo": {
      "@type": "ImageObject",
      "url": siteConfig.logo
    },
    "description": siteConfig.description,
    "sameAs": siteConfig.sameAs,
    "publishingPrinciples": `${siteConfig.url}/editorial-policy`,
    "masthead": `${siteConfig.url}/about`,
    "foundingDate": "2024",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "Dallas-Fort Worth",
      "addressRegion": "TX",
      "addressCountry": "US"
    }
  };
}

/**
 * Generate WebSite schema with SearchAction
 */
function generateWebSiteSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    "name": siteConfig.name,
    "url": siteConfig.url,
    "description": siteConfig.description,
    "publisher": {
      "@type": "NewsMediaOrganization",
      "name": siteConfig.name,
      "logo": {
        "@type": "ImageObject",
        "url": siteConfig.logo
      }
    },
    "potentialAction": {
      "@type": "SearchAction",
      "target": {
        "@type": "EntryPoint",
        "urlTemplate": `${siteConfig.url}/search?q={search_term_string}`
      },
      "query-input": "required name=search_term_string"
    }
  };
}

/**
 * Generate WebPage schema for city sections
 */
function generateWebPageSchema(cityKey, pageTitle, pageDescription) {
  const city = cityConfig[cityKey];
  if (!city) return null;

  return {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "@id": `${city.url}/#webpage`,
    "url": city.url,
    "name": pageTitle || city.name,
    "description": pageDescription || city.description,
    "isPartOf": {
      "@type": "WebSite",
      "name": siteConfig.name,
      "url": siteConfig.url
    },
    "about": {
      "@type": "City",
      "name": city.areaServed.name,
      "containedInPlace": city.areaServed.containedInPlace
    },
    "publisher": {
      "@id": `${siteConfig.url}/#organization`
    }
  };
}

/**
 * Generate NewsArticle schema for articles
 */
function generateNewsArticleSchema(articleData) {
  const {
    headline,
    description,
    url,
    image,
    datePublished,
    dateModified,
    author,
    cityKey = 'arlington'
  } = articleData;

  const city = cityConfig[cityKey];

  return {
    "@context": "https://schema.org",
    "@type": "NewsArticle",
    "@id": `${url}#article`,
    "headline": headline,
    "description": description,
    "url": url,
    "image": image ? {
      "@type": "ImageObject",
      "url": image,
      "width": 1200,
      "height": 630
    } : undefined,
    "datePublished": datePublished,
    "dateModified": dateModified || datePublished,
    "author": {
      "@type": "Person",
      "name": author || "DFWA Social Buzz Staff"
    },
    "publisher": {
      "@id": `${siteConfig.url}/#organization`
    },
    "isPartOf": {
      "@type": "WebPage",
      "@id": `${city.url}/#webpage`
    },
    "articleSection": city.name,
    "inLanguage": "en-US"
  };
}

/**
 * Generate BreadcrumbList schema
 */
function generateBreadcrumbSchema(items) {
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
 * Generate LocalBusiness schema for featured businesses
 */
function generateLocalBusinessSchema(businessData) {
  const {
    name,
    description,
    url,
    telephone,
    address,
    image,
    cityKey = 'arlington'
  } = businessData;

  return {
    "@context": "https://schema.org",
    "@type": "LocalBusiness",
    "name": name,
    "description": description,
    "url": url,
    "telephone": telephone,
    "image": image,
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
      "name": cityConfig[cityKey]?.areaServed?.name || "Arlington"
    }
  };
}

/**
 * Render schema as JSON-LD script tag
 */
function renderSchema(schema) {
  if (!schema) return '';
  
  // Clean up undefined values
  const cleanSchema = JSON.parse(JSON.stringify(schema, (key, value) => {
    return value === undefined ? undefined : value;
  }));

  return `<script type="application/ld+json">\n${JSON.stringify(cleanSchema, null, 2)}\n</script>`;
}

/**
 * Generate all schemas for a page
 */
function generatePageSchemas(pageType, data = {}) {
  const schemas = [];

  switch (pageType) {
    case 'homepage':
      schemas.push(generateOrganizationSchema());
      schemas.push(generateWebSiteSchema());
      break;

    case 'city-home':
      schemas.push(generateOrganizationSchema());
      schemas.push(generateWebSiteSchema());
      schemas.push(generateWebPageSchema(data.cityKey, data.pageTitle, data.pageDescription));
      if (data.breadcrumbs) {
        schemas.push(generateBreadcrumbSchema(data.breadcrumbs));
      }
      break;

    case 'article':
      schemas.push(generateOrganizationSchema());
      schemas.push(generateNewsArticleSchema(data));
      if (data.breadcrumbs) {
        schemas.push(generateBreadcrumbSchema(data.breadcrumbs));
      }
      break;

    case 'business':
      schemas.push(generateOrganizationSchema());
      schemas.push(generateLocalBusinessSchema(data));
      break;

    default:
      schemas.push(generateOrganizationSchema());
      schemas.push(generateWebSiteSchema());
  }

  return schemas.map(renderSchema).join('\n');
}

// Export for use in build process or browser
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    generateOrganizationSchema,
    generateWebSiteSchema,
    generateWebPageSchema,
    generateNewsArticleSchema,
    generateBreadcrumbSchema,
    generateLocalBusinessSchema,
    generatePageSchemas,
    renderSchema
  };
}
