/**
 * DFWA Social Buzz - Build-Time Schema Generator
 * 
 * This script reads article metadata from a JSON file and generates
 * schema-injected HTML files at build time. No runtime DOM manipulation.
 * 
 * Usage: node build-schemas.js
 */

const fs = require('fs');
const path = require('path');
const {
  getPageSchemas,
  renderSchemaScripts,
  validateSchema,
  SITE_CONFIG,
  CITY_CONFIG
} = require('./schema-helpers');

// Configuration
const CONFIG = {
  // Source: Article metadata JSON file (updated by cron/OpenClaw)
  articlesDataPath: path.join(__dirname, '../data/articles-metadata.json'),
  
  // Source: HTML templates directory
  templatesDir: path.join(__dirname, '../templates'),
  
  // Output: Built HTML files
  outputDir: path.join(__dirname, '../arlington/articles'),
  
  // Schema placeholder in templates
  schemaPlaceholder: '<!-- SCHEMA_PLACEHOLDER -->'
};

/**
 * Load articles metadata from JSON file
 * This file is updated by scheduled jobs (cron/OpenClaw)
 */
function loadArticlesMetadata() {
  try {
    if (!fs.existsSync(CONFIG.articlesDataPath)) {
      console.log('No articles metadata file found, creating empty data...');
      return { articles: [], lastUpdated: new Date().toISOString() };
    }
    
    const data = fs.readFileSync(CONFIG.articlesDataPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('Error loading articles metadata:', error.message);
    return { articles: [], lastUpdated: new Date().toISOString() };
  }
}

/**
 * Generate breadcrumbs for an article
 */
function generateBreadcrumbs(article, cityKey = 'arlington') {
  const city = CITY_CONFIG[cityKey];
  
  const crumbs = [
    { name: 'Home', url: SITE_CONFIG.url },
    { name: city.areaServed.city, url: city.url }
  ];
  
  // Add article title (truncated for breadcrumb)
  const shortTitle = article.headline.length > 50 
    ? article.headline.substring(0, 50) + '...'
    : article.headline;
  
  crumbs.push({ name: shortTitle, url: article.url });
  
  return crumbs;
}

/**
 * Build schema for a single article
 */
function buildArticleSchema(article, cityKey = 'arlington') {
  const breadcrumbs = generateBreadcrumbs(article, cityKey);
  
  const schemas = getPageSchemas('article', {
    ...article,
    cityKey,
    breadcrumbs
  });
  
  // Validate all schemas
  const validationResults = schemas.map(validateSchema);
  const hasErrors = validationResults.some(r => !r.valid);
  
  if (hasErrors) {
    console.error(`Schema validation failed for article: ${article.headline}`);
    validationResults.forEach((result, i) => {
      if (!result.valid) {
        console.error(`  Schema ${i}:`, result.errors.join(', '));
      }
    });
    return null;
  }
  
  return renderSchemaScripts(schemas);
}

/**
 * Build a single article HTML file with schema
 */
function buildArticleFile(article, template, cityKey = 'arlington') {
  const schemaHtml = buildArticleSchema(article, cityKey);
  
  if (!schemaHtml) {
    console.error(`Skipping article due to schema errors: ${article.headline}`);
    return null;
  }
  
  // Replace placeholder with schema
  let html = template.replace(CONFIG.schemaPlaceholder, schemaHtml);
  
  // Also replace other template variables
  html = html
    .replace(/\{\{TITLE\}\}/g, article.headline)
    .replace(/\{\{DESCRIPTION\}\}/g, article.description)
    .replace(/\{\{URL\}\}/g, article.url)
    .replace(/\{\{IMAGE\}\}/g, article.image || '')
    .replace(/\{\{DATE_PUBLISHED\}\}/g, article.datePublished)
    .replace(/\{\{AUTHOR\}\}/g, article.author || 'DFWA Social Buzz Staff');
  
  return html;
}

/**
 * Build all article files
 */
function buildAllArticles() {
  console.log('Starting schema build process...\n');
  
  // Load article metadata
  const { articles, lastUpdated } = loadArticlesMetadata();
  console.log(`Loaded ${articles.length} articles (last updated: ${lastUpdated})\n`);
  
  if (articles.length === 0) {
    console.log('No articles to build.');
    return;
  }
  
  // Ensure output directory exists
  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
  }
  
  // Load template
  const templatePath = path.join(CONFIG.templatesDir, 'article-template.html');
  if (!fs.existsSync(templatePath)) {
    console.error(`Template not found: ${templatePath}`);
    console.log('Using inline template...');
    return buildWithInlineTemplate(articles);
  }
  
  const template = fs.readFileSync(templatePath, 'utf8');
  
  // Build each article
  let successCount = 0;
  let errorCount = 0;
  
  for (const article of articles) {
    console.log(`Building: ${article.headline}`);
    
    const cityKey = article.cityKey || 'arlington';
    const html = buildArticleFile(article, template, cityKey);
    
    if (html) {
      // Generate filename from URL or headline
      const filename = article.slug || 
        article.headline.toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-|-$/g, '') + '.html';
      
      const outputPath = path.join(CONFIG.outputDir, filename);
      fs.writeFileSync(outputPath, html);
      console.log(`  ✓ Written: ${outputPath}`);
      successCount++;
    } else {
      errorCount++;
    }
  }
  
  console.log(`\n✓ Build complete: ${successCount} articles, ${errorCount} errors`);
}

/**
 * Build with inline template (fallback)
 */
function buildWithInlineTemplate(articles) {
  const inlineTemplate = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{TITLE}} | Arlington Pulse</title>
    <meta name="description" content="{{DESCRIPTION}}">
    ${CONFIG.schemaPlaceholder}
    <style>
        /* Article styles */
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; line-height: 1.6; }
        h1 { color: #FF6B35; }
        .meta { color: #666; font-size: 0.9rem; margin-bottom: 2rem; }
        .content { margin-top: 2rem; }
    </style>
</head>
<body>
    <article>
        <h1>{{TITLE}}</h1>
        <div class="meta">
            Published: {{DATE_PUBLISHED}} | Author: {{AUTHOR}}
        </div>
        <div class="content">
            {{CONTENT}}
        </div>
    </article>
</body>
</html>`;

  for (const article of articles) {
    console.log(`Building: ${article.headline}`);
    
    const cityKey = article.cityKey || 'arlington';
    const html = buildArticleFile(article, inlineTemplate, cityKey);
    
    if (html) {
      const filename = article.slug || 
        article.headline.toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-|-$/g, '') + '.html';
      
      const outputPath = path.join(CONFIG.outputDir, filename);
      fs.writeFileSync(outputPath, html);
      console.log(`  ✓ Written: ${outputPath}`);
    }
  }
}

/**
 * Generate example articles metadata file
 */
function generateExampleMetadata() {
  const example = {
    lastUpdated: new Date().toISOString(),
    articles: [
      {
        headline: "5 Downtown Arlington Hidden Gems You Need to Discover",
        description: "From craft breweries to vintage arcades and local eateries — discover the best-kept secrets in the heart of The American Dream City.",
        url: "https://arlington.dfwasocialbuzz.com/articles/downtown-arlington-hidden-gems.html",
        slug: "downtown-arlington-hidden-gems.html",
        image: "https://arlington.dfwasocialbuzz.com/images/downtown-gems.jpg",
        datePublished: "2024-06-28T10:00:00-06:00",
        dateModified: "2024-06-28T10:00:00-06:00",
        author: "DFWA Social Buzz Staff",
        cityKey: "arlington",
        content: "<p>Article content goes here...</p>"
      }
    ]
  };
  
  const examplePath = path.join(__dirname, '../data/articles-metadata.example.json');
  fs.mkdirSync(path.dirname(examplePath), { recursive: true });
  fs.writeFileSync(examplePath, JSON.stringify(example, null, 2));
  console.log(`Example metadata written to: ${examplePath}`);
}

// CLI
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.includes('--example')) {
    generateExampleMetadata();
  } else {
    buildAllArticles();
  }
}

module.exports = {
  buildAllArticles,
  buildArticleSchema,
  generateExampleMetadata,
  CONFIG
};
