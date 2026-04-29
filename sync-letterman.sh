#!/bin/bash
# Letterman to Vercel Sync Script
# This script pulls articles from Letterman and updates Vercel pages

# Configuration
LETTERMAN_API="https://api.letterman.ai/api/ai"
API_TOKEN=$(cat ~/.openclaw/secrets/letterman-api-token.txt)
VERCEL_DIR="/root/.openclaw/workspace/dfwa-vercel"

# Publication IDs
ARLINGTON_PUB="69ee9d94a166af267eb5e972"
DALLAS_PUB="69ee9da5a166af267eb5e999"
FORT_WORTH_PUB="69ee9da6a166af267eb5e99e"

# Function to fetch articles from Letterman
fetch_articles() {
    local pub_id=$1
    local limit=${2:-6}
    
    curl -s "${LETTERMAN_API}/newsletters-storage/${pub_id}/newsletters?type=ARTICLE&limit=${limit}" \
        -H "Authorization: Bearer ${API_TOKEN}" \
        -H "Content-Type: application/json"
}

# Function to generate HTML article card
generate_article_card() {
    local title=$1
    local date=$2
    local excerpt=$3
    local url=$4
    
    cat << EOF
            <div class="issue-card">
                <h4>${title}</h4>
                <div class="date">${date}</div>
                <p>${excerpt}</p>
                <a href="${url}" target="_blank">Read Issue →</a>
            </div>
EOF
}

# Fetch articles for each city
echo "Fetching Arlington articles..."
ARLINGTON_ARTICLES=$(fetch_articles $ARLINGTON_PUB)

echo "Fetching Dallas articles..."
DALLAS_ARTICLES=$(fetch_articles $DALLAS_PUB)

echo "Fetching Fort Worth articles..."
FORT_WORTH_ARTICLES=$(fetch_articles $FORT_WORTH_PUB)

# TODO: Parse JSON and generate updated HTML files
# TODO: Deploy to Vercel

echo "Articles fetched successfully"
echo "Next: Parse JSON and update HTML templates"