#!/bin/bash

# Setup script for REAL automated deployments on macOS

echo "🚀 Setting up REAL automated deployment system..."

# Get the current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Create the launch agent plist file
PLIST_PATH="$HOME/Library/LaunchAgents/com.nycodcv.autodeployer.plist"

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nycodcv.autodeployer</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$SCRIPT_DIR/auto_deploy_daemon.sh</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>$SCRIPT_DIR</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>StartInterval</key>
    <integer>300</integer>
    
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/deploy_daemon.log</string>
    
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/deploy_daemon_error.log</string>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

# Create the daemon script
cat > "$SCRIPT_DIR/auto_deploy_daemon.sh" << 'EOF'
#!/bin/bash

# Auto deployment daemon - runs every 5 minutes
cd "$(dirname "$0")"

echo "[$(date)] Auto-deploy check starting..."

# Check if there are any changes in the git repo
git fetch origin

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date)] Remote changes detected, pulling..."
    git pull origin main
fi

# Check for local changes
if [[ -n $(git status -s) ]]; then
    echo "[$(date)] Local changes detected, running smart deploy..."
    ./deploy_smart.sh auto
else
    echo "[$(date)] No changes to deploy"
fi

echo "[$(date)] Auto-deploy check complete"
EOF

chmod +x "$SCRIPT_DIR/auto_deploy_daemon.sh"

# Load the launch agent
launchctl unload "$PLIST_PATH" 2>/dev/null
launchctl load "$PLIST_PATH"

echo "✅ Automated deployment system installed!"
echo ""
echo "The system will now:"
echo "  • Check for changes every 5 minutes"
echo "  • Auto-deploy homepage changes immediately"
echo "  • Batch report changes (5+ changes trigger regeneration)"
echo "  • Prevent overlapping deployments"
echo ""
echo "To check status:"
echo "  launchctl list | grep nycodcv"
echo ""
echo "To view logs:"
echo "  tail -f deploy_daemon.log"
echo ""
echo "To stop auto-deployment:"
echo "  launchctl unload ~/Library/LaunchAgents/com.nycodcv.autodeployer.plist"
echo ""
echo "To restart auto-deployment:"
echo "  launchctl load ~/Library/LaunchAgents/com.nycodcv.autodeployer.plist"