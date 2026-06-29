/**
 * API endpoint to update article metadata
 * Called by Vercel Cron or OpenClaw scheduled task
 * Updates data/articles-metadata.json which is read at build time
 * 
 * Endpoint: POST /api/update-articles
 * Cron: 0 */6 * * * (every 6 hours)
 */

import { kv } from '@vercel/kv';

export default async function handler(req, res) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Verify cron secret if configured
  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret) {
    const authHeader = req.headers.authorization;
    if (!authHeader || authHeader !== `Bearer ${cronSecret}`) {
      return res.status(401).json({ error: 'Unauthorized' });
    }
  }

  try {
    // Fetch new articles from your source (CMS, spreadsheet, Letterman, etc.)
    // This is where you'd integrate with your actual article source
    const newArticles = await fetchNewArticles();
    
    // Get existing metadata
    const existingData = await getArticlesMetadata();
    
    // Merge and deduplicate
    const mergedArticles = mergeArticles(existingData.articles, newArticles);
    
    // Update metadata
    const updatedData = {
      lastUpdated: new Date().toISOString(),
      articles: mergedArticles
    };
    
    // Save to KV store (or file system in development)
    await saveArticlesMetadata(updatedData);
    
    // Trigger rebuild if using on-demand revalidation
    if (process.env.VERCEL_REVALIDATE_TOKEN) {
      await triggerRebuild();
    }
    
    return res.status(200).json({
      success: true,
      message: `Updated ${newArticles.length} articles`,
      totalArticles: mergedArticles.length,
      lastUpdated: updatedData.lastUpdated
    });
    
  } catch (error) {
    console.error('Update articles error:', error);
    return res.status(500).json({
      success: false,
      error: error.message
    });
  }
}

/**
 * Fetch new articles from your source
 * Replace this with your actual integration (Letterman API, CMS, etc.)
 */
async function fetchNewArticles() {
  // Example: Fetch from Letterman API
  // const response = await fetch('https://api.letterman.ai/v1/articles?publication=arlington-pulse');
  // return await response.json();
  
  // Example: Fetch from Google Sheets
  // const response = await fetch(`https://sheets.googleapis.com/v4/spreadsheets/${SHEET_ID}/values/Articles`);
  // return formatSheetData(await response.json());
  
  // Placeholder: Return empty array
  return [];
}

/**
 * Get existing articles metadata
 */
async function getArticlesMetadata() {
  try {
    // Try KV store first (Vercel)
    const data = await kv.get('articles-metadata');
    if (data) return data;
  } catch (e) {
    // KV not available, try file system
  }
  
  // Fallback: Read from file (Node.js)
  try {
    const fs = await import('fs');
    const path = await import('path');
    const filePath = path.join(process.cwd(), 'data', 'articles-metadata.json');
    
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8');
      return JSON.parse(content);
    }
  } catch (e) {
    console.error('Error reading metadata file:', e);
  }
  
  return { articles: [], lastUpdated: null };
}

/**
 * Save articles metadata
 */
async function saveArticlesMetadata(data) {
  // Try KV store first
  try {
    await kv.set('articles-metadata', data);
    return;
  } catch (e) {
    // KV not available
  }
  
  // Fallback: Write to file
  try {
    const fs = await import('fs');
    const path = await import('path');
    const filePath = path.join(process.cwd(), 'data', 'articles-metadata.json');
    
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2));
  } catch (e) {
    console.error('Error saving metadata:', e);
    throw e;
  }
}

/**
 * Merge articles, keeping newest version of duplicates
 */
function mergeArticles(existing, newArticles) {
  const articleMap = new Map();
  
  // Add existing articles
  existing.forEach(article => {
    articleMap.set(article.url, article);
  });
  
  // Add/update with new articles
  newArticles.forEach(article => {
    const existing = articleMap.get(article.url);
    
    if (!existing || new Date(article.dateModified) > new Date(existing.dateModified)) {
      articleMap.set(article.url, article);
    }
  });
  
  return Array.from(articleMap.values());
}

/**
 * Trigger on-demand revalidation (if using Next.js ISR)
 */
async function triggerRebuild() {
  try {
    await fetch(`${process.env.VERCEL_URL}/api/revalidate`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${process.env.VERCEL_REVALIDATE_TOKEN}`
      }
    });
  } catch (e) {
    console.log('Rebuild trigger failed (non-critical):', e.message);
  }
}
