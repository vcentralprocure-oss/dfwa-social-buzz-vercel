#!/usr/bin/env node
/**
 * Meta Links Audit - Check all URLs in meta tags, Open Graph, Twitter Cards, JSON-LD
 */

const fs = require('fs');
const path = require('path');

const articlesDir = path.join(__dirname, 'arlington', 'articles');
const files = fs.readdirSync(articlesDir).filter(f => f.endsWith('.html') && f !== 'index.html');

console.log('='.repeat(100));
console.log('META LINKS AUDIT - Arlington Pulse Articles');
console.log('='.repeat(100));
console.log();

const results = [];

files.forEach(file => {
    const filePath = path.join(articlesDir, file);
    const content = fs.readFileSync(filePath, 'utf8');
    
    // Extract og:url
    const ogUrlMatch = content.match(/<meta property="og:url" content="([^"]+)"/);
    // Extract twitter:url (if exists)
    const twitterUrlMatch = content.match(/<meta name="twitter:url" content="([^"]+)"/);
    // Extract JSON-LD mainEntityOfPage @id
    const jsonLdMatch = content.match(/"mainEntityOfPage":\s*{[^}]*"@id":\s*"([^"]+)"/);
    // Extract any other URLs in meta tags
    const canonicalMatch = content.match(/<link rel="canonical" href="([^"]+)"/);
    
    const ogUrl = ogUrlMatch ? ogUrlMatch[1] : null;
    const jsonLdUrl = jsonLdMatch ? jsonLdMatch[1] : null;
    const canonicalUrl = canonicalMatch ? canonicalMatch[1] : null;
    
    // Check if URLs match expected pattern
    const expectedPath = `/arlington/articles/${file}`;
    const expectedUrl = `https://arlington.dfwasocialbuzz.com${expectedPath}`;
    
    const issues = [];
    
    if (ogUrl && !ogUrl.includes('/arlington/articles/')) {
        issues.push(`og:url missing /arlington/ prefix: ${ogUrl}`);
    }
    
    if (jsonLdUrl && !jsonLdUrl.includes('/arlington/articles/')) {
        issues.push(`JSON-LD @id missing /arlington/ prefix: ${jsonLdUrl}`);
    }
    
    if (canonicalUrl && !canonicalUrl.includes('/arlington/articles/')) {
        issues.push(`Canonical missing /arlington/ prefix: ${canonicalUrl}`);
    }
    
    results.push({
        file,
        ogUrl,
        jsonLdUrl,
        canonicalUrl,
        expectedUrl,
        hasIssues: issues.length > 0,
        issues
    });
});

// Print results
console.log(`Audited ${results.length} article files\n`);

const withIssues = results.filter(r => r.hasIssues);
const clean = results.filter(r => !r.hasIssues);

console.log(`Files with URL issues: ${withIssues.length}`);
console.log(`Files with correct URLs: ${clean.length}`);
console.log();

if (withIssues.length > 0) {
    console.log('ISSUES FOUND:');
    console.log('-'.repeat(100));
    
    withIssues.forEach(r => {
        console.log(`\n📄 ${r.file}`);
        console.log(`   Expected: ${r.expectedUrl}`);
        if (r.ogUrl) console.log(`   og:url:   ${r.ogUrl}`);
        if (r.jsonLdUrl) console.log(`   JSON-LD:  ${r.jsonLdUrl}`);
        if (r.canonicalUrl) console.log(`   Canonical: ${r.canonicalUrl}`);
        console.log('   Issues:');
        r.issues.forEach(issue => console.log(`     ❌ ${issue}`));
    });
}

console.log();
console.log('='.repeat(100));
console.log('SUMMARY');
console.log('='.repeat(100));
console.log();

if (withIssues.length === 0) {
    console.log('✅ All meta URLs are correctly formatted with /arlington/articles/ prefix');
} else {
    console.log(`⚠️  ${withIssues.length} files have incorrect meta URLs`);
    console.log();
    console.log('PROBLEM:');
    console.log('  Meta URLs (og:url, JSON-LD @id) are missing the /arlington/ path prefix.');
    console.log('  This causes 404s when social platforms or search engines try to access them.');
    console.log();
    console.log('SOLUTION:');
    console.log('  Update meta URLs from:');
    console.log('    https://arlington.dfwasocialbuzz.com/articles/SLUG.html');
    console.log('  To:');
    console.log('    https://arlington.dfwasocialbuzz.com/arlington/articles/SLUG.html');
}

// Save results
fs.writeFileSync(
    path.join(__dirname, 'meta-audit-results.json'),
    JSON.stringify(results, null, 2)
);

console.log();
console.log('Results saved to: meta-audit-results.json');
