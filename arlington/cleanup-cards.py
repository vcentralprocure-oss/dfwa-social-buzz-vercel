#!/usr/bin/env python3
"""
Cleanup script to remove cards with raw OC metadata from index.html

This is a ONE-TIME cleanup for existing bad cards.
Future cards will be clean thanks to the pipeline fix.
"""

import re
import sys
from datetime import datetime

INDEX_PATH = "./index.html"

def has_raw_oc_metadata(card_html):
    """Check if card contains raw OC metadata that should never be public."""
    oc_markers = [
        "PUBLICATION:",
        "AUDIENCE VOICE:",
        "TOPIC:",
        "SOURCE URL:",
        "WORD COUNT:",
        "FORMAT:",
        "TONE:",
        "DO NOT:"
    ]
    return any(marker in card_html for marker in oc_markers)

def is_clean_card(card_html):
    """Check if card is properly formatted (manual/clean entry)."""
    # Clean cards have natural dates like "July 9, 2026" not "2026-07-09"
    date_match = re.search(r'<div class="date">([^<]+)</div>', card_html)
    if date_match:
        date_str = date_match.group(1)
        # ISO format dates (2026-07-09) indicate auto-generated bad cards
        if re.match(r'\d{4}-\d{2}-\d{2}$', date_str.strip()):
            return False
    return True

def cleanup_index_html():
    """Remove bad cards and report statistics."""
    
    with open(INDEX_PATH, 'r') as f:
        content = f.read()
    
    # Find all issue cards
    card_pattern = r'<div class="issue-card"[^>]*>.*?(?=<div class="issue-card"|$)'
    cards = re.findall(card_pattern, content, re.DOTALL)
    
    # Also find the last card (pattern above misses it)
    full_card_pattern = r'(<div class="issue-card"[^>]*>.*?</div>\s*(?:<a href="[^"]*">Read Issue →</a>|</div>\s*<span class="coming-soon">))'
    cards = re.findall(full_card_pattern, content, re.DOTALL)
    
    print(f"Found {len(cards)} total cards")
    
    bad_cards = []
    good_cards = []
    
    for card in cards:
        card_html = card[0] if isinstance(card, tuple) else card
        if has_raw_oc_metadata(card_html) or not is_clean_card(card_html):
            bad_cards.append(card_html)
        else:
            good_cards.append(card_html)
    
    print(f"Bad cards (with OC metadata): {len(bad_cards)}")
    print(f"Good cards (clean): {len(good_cards)}")
    
    if not bad_cards:
        print("\n✓ No bad cards found! Index is clean.")
        return
    
    # Show sample of what will be removed
    print("\n--- Sample bad cards to be removed ---")
    for i, card in enumerate(bad_cards[:3], 1):
        title_match = re.search(r'<h4>([^<]+)</h4>', card)
        title = title_match.group(1) if title_match else "Unknown"
        print(f"{i}. {title[:60]}...")
    if len(bad_cards) > 3:
        print(f"... and {len(bad_cards) - 3} more")
    
    # Create new content with only good cards
    # Find the archive-grid section
    grid_start = content.find('<div class="archive-grid">')
    grid_end = content.find('</div>', grid_start) + 6
    
    # Actually we need to be smarter - rebuild the archive-grid section
    # Find where archive-grid starts and where it ends (before view-all-link)
    archive_match = re.search(
        r'(<div class="archive-grid">)(.*?)(<div class="view-all-link">)',
        content,
        re.DOTALL
    )
    
    if not archive_match:
        print("ERROR: Could not find archive-grid section")
        return
    
    # Build new archive-grid content with only good cards
    new_grid_content = '<div class="archive-grid">\n            '
    
    for card in good_cards:
        # Clean up indentation
        cleaned_card = card.strip()
        new_grid_content += cleaned_card + '\n            '
    
    new_grid_content += '<div class="view-all-link">'
    
    # Replace in content
    new_content = content[:archive_match.start()] + new_grid_content + content[archive_match.end():]
    
    # Backup original
    backup_path = INDEX_PATH + f".backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    with open(backup_path, 'w') as f:
        f.write(content)
    print(f"\n✓ Backup saved to: {backup_path}")
    
    # Write cleaned version
    with open(INDEX_PATH, 'w') as f:
        f.write(new_content)
    print(f"✓ Cleaned index written to: {INDEX_PATH}")
    print(f"\nSummary:")
    print(f"  - Removed: {len(bad_cards)} bad cards")
    print(f"  - Kept: {len(good_cards)} clean cards")
    print(f"  - Total: {len(good_cards)} cards remaining")

if __name__ == "__main__":
    print("=" * 60)
    print("Arlington Pulse Card Cleanup")
    print("=" * 60)
    print()
    
    confirm = input("This will remove cards with raw OC metadata. Proceed? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Aborted.")
        sys.exit(0)
    
    cleanup_index_html()
    
    print()
    print("=" * 60)
    print("Next steps:")
    print("  1. Review the cleaned index.html")
    print("  2. Deploy to verify changes")
    print("  3. Future cards will be clean (pipeline fixed)")
    print("=" * 60)
