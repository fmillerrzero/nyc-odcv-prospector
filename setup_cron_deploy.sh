#!/bin/bash

# Simple cron-based auto deployment setup

echo "⏰ Setting up cron-based auto deployment..."

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create a simple deploy check script
cat > "$SCRIPT_DIR/cron_deploy_check.sh" << 'EOF'
#!/bin/bash

# Change to the project directory
cd /Users/forrestmiller/Desktop/nyc-odcv-prospector

# Log the check
echo "[$(date)] Checking for deployment..." >> deploy_cron.log

# Check if we're already deploying
if [ -f deployment.lock ]; then
    echo "[$(date)] Deployment already in progress, skipping" >> deploy_cron.log
    exit 0
fi

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "[$(date)] Found uncommitted changes, deploying..." >> deploy_cron.log
    ./deploy_smart.sh auto >> deploy_cron.log 2>&1
else
    echo "[$(date)] No changes to deploy" >> deploy_cron.log
fi
EOF

chmod +x "$SCRIPT_DIR/cron_deploy_check.sh"

# Add to crontab (runs every 5 minutes)
CRON_CMD="*/5 * * * * cd $SCRIPT_DIR && ./cron_deploy_check.sh"

# Check if already in crontab
if crontab -l 2>/dev/null | grep -q "cron_deploy_check.sh"; then
    echo "⚠️  Cron job already exists. Updating..."
    # Remove old entry
    crontab -l | grep -v "cron_deploy_check.sh" | crontab -
fi

# Add new cron entry
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "✅ Cron-based auto deployment installed!"
echo ""
echo "The system will now:"
echo "  • Check for changes every 5 minutes"
echo "  • Auto-deploy using the smart deployment system"
echo ""
echo "To view cron jobs:"
echo "  crontab -l"
echo ""
echo "To view deployment logs:"
echo "  tail -f deploy_cron.log"
echo ""
echo "To stop auto-deployment:"
echo "  crontab -l | grep -v 'cron_deploy_check.sh' | crontab -"