#!/usr/bin/env node
/**
 * Arlington Pulse - Read Issue Link Audit
 * Crawls the Latest Issues cards and checks link status
 */

const fs = require('fs');
const path = require('path');

// Extract all issue cards from arlington/index.html
const indexPath = path.join(__dirname, 'arlington', 'index.html');
const indexContent = fs.readFileSync(indexPath, 'utf8');

// Parse issue cards - look for the pattern in archive-grid
const issueCards = [];

// Match both article and div issue cards
const cardRegex = /<(article|div) class="issue-card[^"]*"[^>]*>[\s\S]*?<h4>([^<]+)<\/h4>[\s\S]*?<div class="date">([^<]+)<\/div>[\s\S]*?<a href="([^"]+)">Read Issue →<\/a>/gi;

let match;
while ((match = cardRegex.exec(indexContent)) !== null) {
    const [, tagType, title, date, href] = match;
    issueCards.push({
        title: title.trim(),
        date: date.trim(),
        href: href.trim(),
        source: tagType
    });
}

console.log(`Found ${issueCards.length} issue cards in arlington/index.html\n`);

// Check which article files actually exist
const articlesDir = path.join(__dirname, 'arlington', 'articles');
const existingFiles = fs.readdirSync(articlesDir)
    .filter(f => f.endsWith('.html'))
    .map(f => '/arlington/articles/' + f);

console.log(`Existing article files in repo: ${existingFiles.length}\n`);

// Analyze each link
const results = issueCards.map(card => {
    const expectedFile = card.href;
    const exists = existingFiles.includes(expectedFile);
    
    // Try to find similar files if exact match doesn't exist
    let suggestedFix = null;
    let mismatchType = null;
    
    if (!exists) {
        // Extract slug from href
        const slug = path.basename(expectedFile, '.html');
        
        // Check for common mismatch patterns
        // 1. Missing /arlington/ prefix
        const withoutArlington = expectedFile.replace('/arlington/', '/');
        if (existingFiles.some(f => f === withoutArlington)) {
            mismatchType = 'wrong_prefix';
            suggestedFix = withoutArlington;
        }
        
        // 2. Trailing slash issues
        const withTrailingSlash = expectedFile.replace('.html', '/index.html');
        if (existingFiles.some(f => f.includes(slug))) {
            const similar = existingFiles.find(f => f.includes(slug.substring(0, 20)));
            if (similar) {
                mismatchType = 'slug_mismatch';
                suggestedFix = similar;
            }
        }
        
        // 3. Check for partial slug matches
        if (!mismatchType) {
            const slugParts = slug.split('-').slice(0, 5).join('-');
            const partialMatch = existingFiles.find(f => {
                const existingSlug = path.basename(f, '.html');
                return existingSlug.startsWith(slugParts) || slugParts.startsWith(existingSlug.substring(0, 20));
            });
            if (partialMatch) {
                mismatchType = 'partial_slug_match';
                suggestedFix = partialMatch;
            }
        }
        
        if (!mismatchType) {
            mismatchType = 'file_not_found';
        }
    }
    
    return {
        ...card,
        exists,
        statusCode: exists ? 200 : 404,
        mismatchType,
        suggestedFix
    };
});

// Print report
console.log('='.repeat(100));
console.log('ARLINGTON PULSE - READ ISSUE LINK AUDIT REPORT');
console.log('='.repeat(100));
console.log();

console.log('DESKTOP & MOBILE CARDS (Latest Issues Section)');
console.log('-'.repeat(100));
console.log();

const brokenLinks = results.filter(r => !r.exists);
const workingLinks = results.filter(r => r.exists);

console.log(`✅ Working Links: ${workingLinks.length}`);
console.log(`❌ Broken Links (404): ${brokenLinks.length}`);
console.log();

// Detailed breakdown
console.log('DETAILED LINK STATUS:');
console.log('-'.repeat(100));

results.forEach((result, i) => {
    const status = result.exists ? '✅ 200' : '❌ 404';
    console.log(`\n${i + 1}. ${status} | ${result.title.substring(0, 50)}${result.title.length > 50 ? '...' : ''}`);
    console.log(`   Date: ${result.date}`);
    console.log(`   Href: ${result.href}`);
    if (!result.exists) {
        console.log(`   Issue: ${result.mismatchType}`);
        if (result.suggestedFix) {
            console.log(`   Suggested Fix: ${result.suggestedFix}`);
        }
    }
});

console.log();
console.log('='.repeat(100));
console.log('BROKEN LINK ANALYSIS');
console.log('='.repeat(100));
console.log();

// Group by mismatch type
const byType = {};
brokenLinks.forEach(link => {
    const type = link.mismatchType || 'unknown';
    if (!byType[type]) byType[type] = [];
    byType[type].push(link);
});

Object.entries(byType).forEach(([type, links]) => {
    console.log(`\n${type.toUpperCase().replace(/_/g, ' ')} (${links.length} links):`);
    links.forEach(link => {
        console.log(`  - ${link.href}`);
        if (link.suggestedFix) {
            console.log(`    → Should be: ${link.suggestedFix}`);
        }
    });
});

console.log();
console.log('='.repeat(100));
console.log('EXISTING ARTICLE FILES IN REPO');
console.log('='.repeat(100));
console.log();
existingFiles.sort().forEach(f => console.log(`  ${f}`));

// Export JSON for further processing
const auditResults = {
    timestamp: new Date().toISOString(),
    totalCards: issueCards.length,
    working: workingLinks.length,
    broken: brokenLinks.length,
    results,
    existingFiles
};

fs.writeFileSync(
    path.join(__dirname, 'link-audit-results.json'),
    JSON.stringify(auditResults, null, 2)
);

console.log();
console.log('Audit results saved to: link-audit-results.json');
