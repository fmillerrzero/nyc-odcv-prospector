#!/bin/bash

echo "🚀 Force Render.com Redeployment Script"
echo "======================================="
echo ""
echo "This script will help you force a fresh deployment on Render.com"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Option 1: Manual Dashboard Method (Recommended)${NC}"
echo "1. Go to your Render Dashboard: https://dashboard.render.com"
echo "2. Find your static site service"
echo "3. Click on 'Manual Deploy' dropdown"
echo "4. Select 'Clear build cache & deploy'"
echo "5. This will force a complete rebuild without any cached files"
echo ""

echo -e "${YELLOW}Option 2: Add Cache-Busting to HTML Files${NC}"
echo "Running cache-busting script..."
python3 add_cache_busting.py

echo ""
echo -e "${YELLOW}Option 3: Create a Dummy Commit${NC}"
echo "Creating a deployment trigger file..."

# Create or update a deployment trigger file
echo "Deployment triggered at: $(date)" > .deployment-trigger
git add .deployment-trigger
git commit -m "Force deployment: $(date '+%Y-%m-%d %H:%M:%S')"
git push origin main

echo ""
echo -e "${YELLOW}Option 4: Use Smart Deploy with Force Flag${NC}"
echo "You can also use: ./deploy_smart.sh reports"
echo "This will regenerate all reports and deploy"
echo ""

echo -e "${GREEN}Additional Tips:${NC}"
echo "1. If cached content persists, try accessing with ?v=$(date +%s) query parameter"
echo "2. Clear your browser cache (Cmd+Shift+R on Mac, Ctrl+Shift+R on Windows)"
echo "3. Use incognito/private browsing to test without local cache"
echo "4. Check Render logs for deployment status"
echo ""

echo -e "${YELLOW}CDN Cache Clearing:${NC}"
echo "Render claims to invalidate CDN caches immediately, but if issues persist:"
echo "1. Wait 5-10 minutes for global CDN propagation"
echo "2. Try accessing from different locations/networks"
echo "3. Use a VPN to test from different geographic locations"