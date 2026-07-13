# Issue Card OC Metadata Mapping

## Problem
Issue cards are currently displaying raw OC metadata in the description:
```html
<p>PUBLICATION: Arlington Pulse — DFWA Social Buzz
QUADRANT: ALL
AUDIENCE VOICE: neutral city voice, broad Arlington resident appeal
TOPIC: FC Dallas' Pe...</p>
```

## Solution
Map OC fields to front-end display elements:

| OC Field | Front-End Element | Example Output |
|----------|-------------------|----------------|
| `QUADRANT: NORTH/SOUTH/CENTRAL/EAST/ALL` | Badge + `data-quadrant` attribute | `<span class="quadrant-badge north">NORTH</span>` |
| `TOPIC: X` | Visible topic/description line | `FC Dallas' Petar Musa named to 2026 MLS All-Star team` |
| `PUBLICATION: X` | Publication attribution | `Arlington Pulse` |

## Implementation

### Option 1: JavaScript Auto-Transform (Recommended)
Include the `oc-card-mapper.js` script in your HTML:

```html
<script src="oc-card-mapper.js"></script>
```

This automatically parses and transforms all cards on page load.

### Option 2: Manual HTML Update
Update cards to this structure:

```html
<div class="issue-card" data-quadrant="north">
    <span class="quadrant-badge north">NORTH</span>
    <h4>Tormenta Rampaging Run: Six Flags Over Texas' newest roller coaster opens</h4>
    <div class="date">2026-07-09</div>
    <p>Professional tone coverage of entertainment venues and attractions — Arlington Pulse</p>
    <a href="/arlington/articles/tormenta-rampaging-run-six-flags-over-te.html">Read Issue →</a>
</div>
```

### Option 3: Server-Side Rendering
If generating cards from a CMS/API, map fields before output:

```javascript
const cardData = {
    quadrant: ocData.quadrant.toLowerCase(), // 'north', 'south', etc.
    topic: ocData.topic, // Short topic line
    publication: ocData.publication.split('—')[0].trim(), // 'Arlington Pulse'
    headline: ocData.headline,
    date: ocData.date,
    url: ocData.url
};
```

## Badge CSS Classes

```css
.quadrant-badge.north { background: #3B82F6; color: #fff; }
.quadrant-badge.south { background: #22C55E; color: #fff; }
.quadrant-badge.central { background: #A855F7; color: #fff; }
.quadrant-badge.east { background: #F59E0B; color: #000; }
.quadrant-badge.all { background: #FF6B35; color: #fff; }
```

## Filter Button Integration

The `data-quadrant` attribute enables filtering:

```javascript
document.querySelectorAll('.qfilter-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const filter = this.dataset.filter;
        document.querySelectorAll('.issue-card').forEach(card => {
            const q = card.dataset.quadrant || 'all';
            card.style.display = (filter === 'all' || q === filter) ? '' : 'none';
        });
    });
});
```

## Before/After Example

### Before (Raw OC Metadata)
```html
<div class="issue-card" data-quadrant="all">
    <span class="quadrant-badge all">ALL</span>
    <h4>FC Dallas' Petar Musa named to 2026 MLS All-Star team</h4>
    <div class="date">2026-07-09</div>
    <p>PUBLICATION: Arlington Pulse — DFWA Social Buzz
    QUADRANT: ALL
    AUDIENCE VOICE: neutral city voice, broad Arlington resident appeal
    TOPIC: FC Dallas' Pe...</p>
    <a href="...">Read Issue →</a>
</div>
```

### After (Mapped)
```html
<div class="issue-card" data-quadrant="all">
    <span class="quadrant-badge all">ALL</span>
    <h4>FC Dallas' Petar Musa named to 2026 MLS All-Star team</h4>
    <div class="date">2026-07-09</div>
    <p>FC Dallas' Petar Musa named to 2026 MLS All-Star team — Arlington Pulse</p>
    <a href="...">Read Issue →</a>
</div>
```

## Files Updated
- `oc-card-mapper.js` - Auto-transformation script
- `index.html` - Include the script tag before closing `</body>`
