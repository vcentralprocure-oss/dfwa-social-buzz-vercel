#!/bin/bash
# DFWA Daily Article Generator
# Run this script daily to create 1 new article per city

# Configuration
LETTERMAN_API="https://api.letterman.ai/api/ai"
API_TOKEN=$(cat ~/.openclaw/secrets/letterman-api-token.txt)
VERCEL_DIR="/root/.openclaw/workspace/dfwa-vercel"

# Publication IDs
ARLINGTON_PUB="69ee9d94a166af267eb5e972"
DALLAS_PUB="69ee9da5a166af267eb5e999"
FORT_WORTH_PUB="69ee9da6a166af267eb5e99e"

# Function to create article
create_article() {
    local pub_id=$1
    local city=$2
    local topic=$3
    
    echo "Creating article for $city: $topic"
    
    # This would call the Letterman API to create article
    # For now, this is a template that needs to be run manually
    
    echo "Article created for $city"
}

# Daily topics (rotate through these)
DAY_OF_WEEK=$(date +%u)

case $DAY_OF_WEEK in
    1) # Monday
        ARLINGTON_TOPIC="Weekend Recap: What You Missed"
        DALLAS_TOPIC="Monday Motivation: Coffee Shop Guide"
        FORT_WORTH_TOPIC="Stockyards Weekend Roundup"
        ;;
    2) # Tuesday
        ARLINGTON_TOPIC="New Restaurant Alert"
        DALLAS_TOPIC="Taco Tuesday: Best Spots"
        FORT_WORTH_TOPIC="BBQ Tuesday: Smoked Meats"
        ;;
    3) # Wednesday
        ARLINGTON_TOPIC="UTA Campus Events"
        DALLAS_TOPIC="Midweek Date Night Ideas"
        FORT_WORTH_TOPIC="West 7th Wednesday"
        ;;
    4) # Thursday
        ARLINGTON_TOPIC="Entertainment District Update"
        DALLAS_TOPIC="Thirsty Thursday: Breweries"
        FORT_WORTH_TOPIC="Live Music Tonight"
        ;;
    5) # Friday
        ARLINGTON_TOPIC="Weekend Guide: What's Happening"
        DALLAS_TOPIC="Friday Night Plans"
        FORT_WORTH_TOPIC="Weekend in the Stockyards"
        ;;
    6) # Saturday
        ARLINGTON_TOPIC="Saturday Morning Markets"
        DALLAS_TOPIC="Weekend Brunch Guide"
        FORT_WORTH_TOPIC="Saturday at the Trails"
        ;;
    7) # Sunday
        ARLINGTON_TOPIC="Sunday Funday: Family Activities"
        DALLAS_TOPIC="Sunday Brunch Spots"
        FORT_WORTH_TOPIC="Sunday BBQ Guide"
        ;;
esac

echo "=========================================="
echo "DFWA Daily Article Generator"
echo "Date: $(date)"
echo "=========================================="
echo ""
echo "Today's Topics:"
echo "  Arlington: $ARLINGTON_TOPIC"
echo "  Dallas: $DALLAS_TOPIC"
echo "  Fort Worth: $FORT_WORTH_TOPIC"
echo ""
echo "To create articles, run:"
echo "  openclaw sessions-spawn --task 'Create Arlington article about $ARLINGTON_TOPIC'"
echo "  openclaw sessions-spawn --task 'Create Dallas article about $DALLAS_TOPIC'"
echo "  openclaw sessions-spawn --task 'Create Fort Worth article about $FORT_WORTH_TOPIC'"
echo ""
echo "Or manually create in Letterman and update Vercel pages."