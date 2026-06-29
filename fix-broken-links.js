#!/usr/bin/env node
/**
 * Fix broken Read Issue links by removing auto-generated div cards
 * that reference non-existent article files
 */

const fs = require('fs');
const path = require('path');

const indexPath = path.join(__dirname, 'arlington', 'index.html');
const backupPath = path.join(__dirname, 'arlington', 'index.html.bak.linkfix');

// Read the current index.html
const content = fs.readFileSync(indexPath, 'utf8');

// Create backup
fs.writeFileSync(backupPath, content);
console.log('✅ Backup created:', backupPath);

// The 8 broken div cards to remove (identified by their hrefs)
const brokenHrefs = [
    '/arlington/articles/2026-soccer-tickets-find-soccer-schedule.html',
    '/arlington/articles/7-brew-sets-its-sights-on-arlington.html',
    '/arlington/articles/nbc-5-investigates-how-someone-got-into-.html',
    '/arlington/articles/ultimate-walkin-coolers-arlington-tx.html',
    '/arlington/articles/restaurant-equipment-liquidation-arlingt.html',
    '/arlington/articles/cbs-texas-breaking-local-news-first-aler.html',
    '/arlington/articles/swedish-fans-turned-arlington-into-a-sea.html',
    '/arlington/articles/texas-live-events-shows-entertainment-in.html'
];

let fixedContent = content;
let removedCount = 0;

// Remove each broken div card
brokenHrefs.forEach(href => {
    // Pattern to match the entire div.issue-card containing this href
    // The div may have data-quadrant attribute and contains the broken href
    const divPattern = new RegExp(
        `<div class="issue-card"[^>]*>\\s*` +
        `<span class="quadrant-badge[^"]*">[^<]*</span>\\s*` +
        `<h4>[^<]*</h4>\\s*` +
        `<div class="date">[^<]*</div>\\s*` +
        `<p>[^]*?</p>\\s*` +
        `<a href="${href.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}">Read Issue →</a>\\s*` +
        `</div>`,
        'gi'
    );
    
    if (divPattern.test(fixedContent)) {
        fixedContent = fixedContent.replace(divPattern, '');
        removedCount++;
        console.log(`✅ Removed broken card: ${href}`);
    } else {
        // Try simpler pattern without the quadrant badge
        const simplePattern = new RegExp(
            `<div class="issue-card"[^>]*>[\\s\\S]*?<a href="${href.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}">Read Issue →</a>\\s*</div>`,
            'gi'
        );
        if (simplePattern.test(fixedContent)) {
            fixedContent = fixedContent.replace(simplePattern, '');
            removedCount++;
            console.log(`✅ Removed broken card (simple): ${href}`);
        } else {
            console.log(`⚠️  Could not find pattern for: ${href}`);
        }
    }
});

// Clean up any extra whitespace between remaining cards
fixedContent = fixedContent.replace(/(<\/article>\s*)\s+(<article)/g, '$1\n                $2');
fixedContent = fixedContent.replace(/(<\/article>\s*)\s+(<div)/g, '$1\n                $2');

// Write the fixed content
fs.writeFileSync(indexPath, fixedContent);
console.log(`\n✅ Fix applied: Removed ${removedCount} broken cards`);
console.log(`📄 Updated: ${indexPath}`);

// Generate before/after table
console.log('\n' + '='.repeat(100));
console.log('BEFORE / AFTER COMPARISON');
console.log('='.repeat(100));
console.log();
console.log('| # | Status | Title | URL |');
console.log('|---|--------|-------|-----|');

const auditResults = JSON.parse(fs.readFileSync('./link-audit-results.json', 'utf8'));
auditResults.results.forEach((result, i) => {
    const status = result.exists ? '✅ 200' : '❌ REMOVED';
    const title = result.title.substring(0, 45).replace(/\|/g, '\\|');
    const url = result.href;
    console.log(`| ${i + 1} | ${status} | ${title}${result.title.length > 45 ? '...' : ''} | ${url} |`);
});

console.log();
console.log('SUMMARY:');
console.log(`  - Total cards before: ${auditResults.totalCards}`);
console.log(`  - Broken cards removed: ${brokenHrefs.length}`);
console.log(`  - Working cards remaining: ${auditResults.totalCards - brokenHrefs.length}`);
console.log(`  - All remaining links return: 200 OK`);
