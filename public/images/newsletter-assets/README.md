# Newsletter Assets Directory

Central storage for reusable images across DFWA Social Buzz newsletters.

## Directory Structure

```
newsletter-assets/
├── shared/           # Images used across ALL city pages + root domain
│   └── logos, headers, footers, brand assets
├── dallas/           # Dallas-specific images
│   └── skyline, neighborhoods, local events
├── fort-worth/       # Fort Worth-specific images
│   └── stockyards, downtown, local spots
└── arlington/        # Arlington-specific images
    └── entertainment district, stadiums, parks
```

## Usage

### For Letterman Articles
When creating articles via the Letterman API, reference images using:
- **Shared assets:** Use for all newsletters (root + city pages)
- **City-specific:** Use only for that city's newsletter

### Image Naming Convention
- Use descriptive names: `header-summer-2026.jpg`
- Include dimensions if relevant: `logo-600x200.png`
- Date versioned for seasonal content: `hero-june-2026.jpg`

### Current Assets

#### Shared
- `file_112---67ad5c2b-00b1-4b6c-b7d1-0cc25569dd1f.jpg` - [Add description]

#### Dallas
- [Add as needed]

#### Fort Worth
- [Add as needed]

#### Arlington
- [Add as needed]

## Storage Locations

- **Local:** `~/.openclaw/workspace/images/newsletter-assets/`
- **Vercel (for web access):** `dfwa-vercel/public/images/`

## Best Practices

1. **Optimize before storing:** Compress images for web (max 200KB for headers, 50KB for thumbnails)
2. **Use consistent dimensions:** Header images should be consistent width (recommended: 1200x630 for social sharing)
3. **Backup originals:** Keep high-res originals in a separate `originals/` folder if needed
4. **Document usage:** Update this README when adding new reusable assets

## Letterman Integration

To use these images in Letterman articles:
1. Upload via Letterman image API: `POST /images` (multipart/form-data)
2. Or host on Vercel and use absolute URLs
3. Reference in article HTML: `<img src="URL" alt="description">`
