/**
 * Script to add JSON-LD schema to existing article HTML files
 * Usage: node add-article-schema.js <article-file.html> [options]
 */

const fs = require('fs');
const path = require('path');

// Schema template for articles
function generateArticleSchema(articleData) {
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

  const cityUrls = {
    arlington: 'https://arlington.dfwasocialbuzz.com',
    dallas: 'https://dallas.dfwasocialbuzz.com',
    fortworth: 'https://fortworth.dfwasocialbuzz.com'
  };

  const cityUrl = cityUrls[cityKey] || cityUrls.arlington;

  return `<!-- NewsMediaOrganization Schema -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "NewsMediaOrganization",
  "@id": "https://dfwasocialbuzz.com/#organization",
  "name": "DFWA Social Buzz",
  "url": "https://dfwasocialbuzz.com",
  "logo": {
    "@type": "ImageObject",
    "url": "https://dfwasocialbuzz.com/logo.png",
    "width": 512,
    "height": 512
  },
  "description": "Your source for local news, events, and community updates across the Dallas-Fort Worth-Arlington metroplex.",
  "sameAs": [
    "https://facebook.com/dfwasocialbuzz",
    "https://twitter.com/dfwasocialbuzz",
    "https://instagram.com/dfwasocialbuzz"
  ],
  "foundingDate": "2024"
}
</script>

<!-- NewsArticle Schema -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "NewsArticle",
  "@id": "${url}#article",
  "headline": "${headline}",
  "description": "${description}",
  "url": "${url}",
  "image": {
    "@type": "ImageObject",
    "url": "${image}",
    "width": 1200,
    "height": 630
  },
  "datePublished": "${datePublished}",
  "dateModified": "${dateModified || datePublished}",
  "author": {
    "@type": "Person",
    "name": "${author || 'DFWA Social Buzz Staff'}"
  },
  "publisher": {
    "@id": "https://dfwasocialbuzz.com/#organization"
  },
  "isPartOf": {
    "@type": "WebPage",
    "@id": "${cityUrl}/#webpage"
  },
  "articleSection": "${cityKey.charAt(0).toUpperCase() + cityKey.slice(1)} Pulse",
  "inLanguage": "en-US",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "${url}"
  }
}
</script>

<!-- BreadcrumbList Schema -->
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://dfwasocialbuzz.com"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "${cityKey.charAt(0).toUpperCase() + cityKey.slice(1))}",
      "item": "${cityUrl}"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "${headline.substring(0, 50)}${headline.length > 50 ? '...' : ''}",
      "item": "${url}"
    }
  ]
}
</script>`;
}

// Extract metadata from HTML content
function extractMetadata(html, filePath) {
  const metadata = {
    headline: '',
    description: '',
    url: '',
    image: '',
    datePublished: new Date().toISOString(),
    author: 'DFWA Social Buzz Staff'
  };

  // Extract title
  const titleMatch = html.match(/<title>(.*?)<\/title>/i);
  if (titleMatch) {
    metadata.headline = titleMatch[1].replace(/\|.*$/, '').trim();
  }

  // Extract meta description
  const descMatch = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']*)["']/i) ||
                     html.match(/<meta[^>]*content=["']([^"']*)["'][^>]*name=["']description["']/i);
  if (descMatch) {
    metadata.description = descMatch[1];
  }

  // Extract first image
  const imgMatch = html.match(/<img[^>]*src=["']([^"']*)["']/i);
  if (imgMatch) {
    metadata.image = imgMatch[1];
    if (!metadata.image.startsWith('http')) {
      metadata.image = 'https://arlington.dfwasocialbuzz.com' + metadata.image;
    }
  } else {
    metadata.image = 'https://dfwasocialbuzz.com/logo.png';
  }

  // Generate URL from file path
  const fileName = path.basename(filePath);
  metadata.url = `https://dfwasocialbuzz.com/arlington/articles/${fileName}`;

  return metadata;
}

// Add schema to HTML file
function addSchemaToFile(filePath, options = {}) {
  console.log(`Processing: ${filePath}`);

  let html = fs.readFileSync(filePath, 'utf8');

  // Check if schema already exists
  if (html.includes('application/ld+json')) {
    console.log('  Schema already exists, skipping...');
    return;
  }

  // Extract metadata
  const metadata = extractMetadata(html, filePath);

  // Override with options
  if (options.headline) metadata.headline = options.headline;
  if (options.description) metadata.description = options.description;
  if (options.image) metadata.image = options.image;
  if (options.date) metadata.datePublished = options.date;
  if (options.author) metadata.author = options.author;

  // Generate schema
  const schema = generateArticleSchema(metadata);

  // Insert after <head> tag
  const headEndMatch = html.match(/<head[^>]*>/i);
  if (headEndMatch) {
    const insertIndex = headEndMatch.index + headEndMatch[0].length;
    html = html.slice(0, insertIndex) + '\n    ' + schema.replace(/\n/g, '\n    ') + '\n' + html.slice(insertIndex);

    // Write back
    fs.writeFileSync(filePath, html);
    console.log('  Schema added successfully!');
  } else {
    console.log('  Error: Could not find <head> tag');
  }
}

// Main execution
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('Usage: node add-article-schema.js <article-file.html> [options]');
    console.log('');
    console.log('Options:');
    console.log('  --headline="Title"     Article headline');
    console.log('  --description="Desc"   Article description');
    console.log('  --image="URL"          Featured image URL');
    console.log('  --date="2024-01-15"    Publication date');
    console.log('  --author="Name"        Author name');
    console.log('');
    console.log('Example:');
    console.log('  node add-article-schema.js articles/my-article.html --headline="My Article" --date="2024-06-15"');
    process.exit(1);
  }

  const filePath = args[0];
  const options = {};

  // Parse options
  args.slice(1).forEach(arg => {
    const match = arg.match(/^--(\w+)=(.+)$/);
    if (match) {
      options[match[1]] = match[2].replace(/^["']|["']$/g, '');
    }
  });

  if (fs.existsSync(filePath)) {
    addSchemaToFile(filePath, options);
  } else {
    console.error(`File not found: ${filePath}`);
    process.exit(1);
  }
}

module.exports = { addSchemaToFile, generateArticleSchema, extractMetadata };
