#!/usr/bin/env node
/**
 * Meta Links Audit v2 - Check all URLs in meta tags using correct base URL
 * Correct base: https://dfwasocialbuzz.com/arlington/articles/
 */

const fs = require('fs');
const path = require('path');

const articlesDir = path.join(__dirname, 'arlington', 'articles');
const files = fs.readdirSync(articlesDir).filter(f => f.endsWith('.html') && f !== 'index.html');

// CORRECT base URL (main domain, not subdomain)
const CORRECT_BASE = 'https://dfwasocialbuzz.com/arlington/articles';
const INCORRECT_BASE = 'https://arlington.dfwasocialbuzz.com';

console.log('='.repeat(100));
console.log('META LINKS AUDIT v2 - Arlington Pulse Articles');
console.log('Correct Base URL:', CORRECT_BASE);
console.log('='.repeat(100));
console.log();

const results = [];

files.forEach(file => {
    const filePath = path.join(articlesDir, file);
    const content = fs.readFileSync(filePath, 'utf8');
    
    // Extract og:url
    const ogUrlMatch = content.match(/<meta property="og:url" content="([^"]+)"/);
    // Extract JSON-LD mainEntityOfPage @id
    const jsonLdMatch = content.match(/"mainEntityOfPage":\s*{[^}]*"@id":\s*"([^"]+)"/);
    // Extract JSON-LD url field
    const jsonLdUrlMatch = content.match(/"url":\s*"(https:\/\/[^"]+)"/);
    
    const ogUrl = ogUrlMatch ? ogUrlMatch[1] : null;
    const jsonLdId = jsonLdMatch ? jsonLdMatch[1] : null;
    const jsonLdUrl = jsonLdUrlMatch ? jsonLdUrlMatch[1] : null;
    
    // Expected correct URL
    const expectedUrl = `${CORRECT_BASE}/${file}`;
    
    const issues = [];
    
    // Check for retired subdomain
    if (ogUrl && ogUrl.includes('arlington.dfwasocialbuzz.com')) {
        issues.push(`og:url uses retired subdomain: ${ogUrl}`);
    }
    if (jsonLdId && jsonLdId.includes('arlington.dfwasocialbuzz.com')) {
        issues.push(`JSON-LD @id uses retired subdomain: ${jsonLdId}`);
    }
    if (jsonLdUrl && jsonLdUrl.includes('arlington.dfwasocialbuzz.com')) {
        issues.push(`JSON-LD url uses retired subdomain: ${jsonLdUrl}`);
    }
    
    // Check if URLs match expected pattern
    if (ogUrl && !ogUrl.includes('/arlington/articles/')) {
        issues.push(`og:url missing /arlington/articles/ path: ${ogUrl}`);
    }
    if (jsonLdId && !jsonLdId.includes('/arlington/articles/')) {
        issues.push(`JSON-LD @id missing /arlington/articles/ path: ${jsonLdId}`);
    }
    
    results.push({
        file,
        ogUrl,
        jsonLdId,
        jsonLdUrl,
        expectedUrl,
        hasIssues: issues.length > 0,
        issues
    });
});

// Print results
console.log(`Audited ${results.length} article files\n`);

const withIssues = results.filter(r => r.hasIssues);
const clean = results.filter(r => !r.hasIssues);
const noSchema = results.filter(r => !r.ogUrl && !r.jsonLdId);

console.log(`Files with URL issues: ${withIssues.length}`);
console.log(`Files with correct URLs: ${clean.length}`);
console.log(`Files without schema: ${noSchema.length}`);
console.log();

if (withIssues.length > 0) {
    console.log('❌ ISSUES FOUND:');
    console.log('-'.repeat(100));
    
    withIssues.forEach(r => {
        console.log(`\n📄 ${r.file}`);
        console.log(`   Expected: ${r.expectedUrl}`);
        if (r.ogUrl) console.log(`   og:url:   ${r.ogUrl}`);
        if (r.jsonLdId) console.log(`   JSON-LD @id: ${r.jsonLdId}`);
        if (r.jsonLdUrl) console.log(`   JSON-LD url: ${r.jsonLdUrl}`);
        console.log('   Issues:');
        r.issues.forEach(issue => console.log(`     ❌ ${issue}`));
    });
}

if (noSchema.length > 0) {
    console.log('\n\n⚠️  FILES WITHOUT SCHEMA (need schema added):');
    console.log('-'.repeat(100));
    noSchema.forEach(r => console.log(`  - ${r.file}`));
}

console.log();
console.log('='.repeat(100));
console.log('SUMMARY');
console.log('='.repeat(100));
console.log();

if (withIssues.length === 0 && noSchema.length === 0) {
    console.log('✅ All meta URLs are correctly using dfwasocialbuzz.com/arlington/articles/');
} else {
    if (withIssues.length > 0) {
        console.log(`❌ ${withIssues.length} files have incorrect meta URLs`);
        console.log();
        console.log('PROBLEMS:');
        console.log('  1. Some URLs use retired subdomain (arlington.dfwasocialbuzz.com)');
        console.log('  2. Some URLs missing /arlington/articles/ path');
        console.log();
        console.log('CORRECT FORMAT:');
        console.log('  https://dfwasocialbuzz.com/arlington/articles/SLUG.html');
    }
    if (noSchema.length > 0) {
        console.log(`\n⚠️  ${noSchema.length} files need schema added`);
    }
}

// Save results
fs.writeFileSync(
    path.join(__dirname, 'meta-audit-results-v2.json'),
    JSON.stringify(results, null, 2)
);

console.log();
console.log('Results saved to: meta-audit-results-v2.json');
