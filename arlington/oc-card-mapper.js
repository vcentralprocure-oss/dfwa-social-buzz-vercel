/**
 * OC Metadata Card Mapper
 * 
 * Maps raw OC metadata fields to front-end display:
 * - QUADRANT → Badge + data-quadrant attribute for filtering
 * - TOPIC → Visible topic line (replaces raw metadata block)
 * - PUBLICATION → Publication attribution line
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        cardSelector: '.issue-card',
        badgeClass: 'quadrant-badge',
        defaultQuadrant: 'all',
        publicationName: 'Arlington Pulse'
    };

    // Quadrant to badge color mapping
    const QUADRANT_STYLES = {
        'north': { class: 'north', label: 'NORTH' },
        'south': { class: 'south', label: 'SOUTH' },
        'central': { class: 'central', label: 'CENTRAL' },
        'east': { class: 'east', label: 'EAST' },
        'all': { class: 'all', label: 'ALL' }
    };

    /**
     * Parse raw OC metadata from card content
     * @param {string} content - Raw card text content
     * @returns {Object} Parsed metadata
     */
    function parseOCMetadata(content) {
        const metadata = {
            quadrant: null,
            topic: null,
            publication: null,
            audienceVoice: null,
            source: null
        };

        // Extract QUADRANT
        const quadrantMatch = content.match(/QUADRANT:\s*(\w+)/i);
        if (quadrantMatch) {
            metadata.quadrant = quadrantMatch[1].toLowerCase();
        }

        // Extract TOPIC (handles multi-line)
        const topicMatch = content.match(/TOPIC:\s*([^\n]+(?:\n(?!(?:QUADRANT|AUDIENCE|SOURCES?):)[^\n]+)*)/i);
        if (topicMatch) {
            metadata.topic = topicMatch[1].trim();
        }

        // Extract PUBLICATION
        const pubMatch = content.match(/PUBLICATION:\s*([^\n]+)/i);
        if (pubMatch) {
            metadata.publication = pubMatch[1].trim();
        }

        // Extract AUDIENCE VOICE
        const voiceMatch = content.match(/AUDIENCE VOICE:\s*([^\n]+(?:\n(?!(?:QUADRANT|TOPIC|SOURCES?):)[^\n]+)*)/i);
        if (voiceMatch) {
            metadata.audienceVoice = voiceMatch[1].trim();
        }

        return metadata;
    }

    /**
     * Transform a single issue card
     * @param {HTMLElement} card - The issue card element
     */
    function transformCard(card) {
        const paragraph = card.querySelector('p');
        if (!paragraph) return;

        const rawContent = paragraph.textContent;
        
        // Check if this card has OC metadata
        if (!rawContent.includes('QUADRANT:') && !rawContent.includes('PUBLICATION:')) {
            return; // Already transformed or no metadata
        }

        const metadata = parseOCMetadata(rawContent);
        
        // Update data-quadrant attribute
        if (metadata.quadrant) {
            card.setAttribute('data-quadrant', metadata.quadrant);
        }

        // Update badge
        const badge = card.querySelector('.' + CONFIG.badgeClass);
        if (badge && metadata.quadrant) {
            const style = QUADRANT_STYLES[metadata.quadrant] || QUADRANT_STYLES.all;
            badge.className = `${CONFIG.badgeClass} ${style.class}`;
            badge.textContent = style.label;
        }

        // Replace raw metadata with clean display
        let newContent = '';
        
        if (metadata.topic) {
            newContent += metadata.topic;
        }
        
        if (metadata.publication) {
            // Extract just the publication name (before the em-dash if present)
            const pubName = metadata.publication.split('—')[0].trim();
            if (newContent) {
                newContent += ` — ${pubName}`;
            } else {
                newContent = pubName;
            }
        }

        // If no parsed content, use a fallback
        if (!newContent) {
            newContent = 'Arlington local news and updates';
        }

        paragraph.textContent = newContent;
    }

    /**
     * Transform all issue cards on the page
     */
    function transformAllCards() {
        const cards = document.querySelectorAll(CONFIG.cardSelector);
        cards.forEach(transformCard);
        console.log(`[OC Mapper] Transformed ${cards.length} issue cards`);
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', transformAllCards);
    } else {
        transformAllCards();
    }

    // Expose for manual re-runs or external use
    window.OCMapper = {
        transform: transformAllCards,
        transformCard: transformCard,
        parseMetadata: parseOCMetadata
    };

})();
