#!/bin/bash

# Smart deployment script that uses the deployment manager

echo "🤖 Smart Deployment System"
echo "========================="

# Check if we're being called with a specific mode
MODE=${1:-auto}

case $MODE in
    homepage)
        echo "🏠 Homepage-only deployment requested..."
        python3 deploy_manager.py homepage
        ;;
    reports)
        echo "📊 Full reports deployment requested..."
        python3 deploy_manager.py reports
        ;;
    auto)
        echo "🤖 Auto mode - smart deployment based on changes..."
        python3 deploy_manager.py auto
        ;;
    status)
        python3 deploy_manager.py status
        ;;
    *)
        echo "Usage: ./deploy_smart.sh [homepage|reports|auto|status]"
        echo ""
        echo "Modes:"
        echo "  homepage - Deploy only index.html changes"
        echo "  reports  - Full report regeneration and deployment"
        echo "  auto     - Smart deployment based on change detection"
        echo "  status   - Show deployment status"
        exit 1
        ;;
esac