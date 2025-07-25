# Smart Deployment System Guide

## Overview

The new deployment system intelligently separates homepage updates from full report regeneration, preventing unnecessary rebuilds and overlapping deployments.

## Key Features

1. **Separate Homepage Deploys**: Homepage can update instantly without regenerating all reports
2. **Change Tracking**: Tracks changes and only regenerates reports after 5+ changes
3. **Deploy Lock**: Prevents overlapping deployments
4. **Cooldown Periods**: 5-minute cooldown between full report deployments
5. **Smart Detection**: Automatically detects what changed (homepage, reports, or code)

## Usage

### Quick Commands

```bash
# Smart auto-deployment (recommended)
./deploy_smart.sh

# Deploy only homepage changes
./deploy_smart.sh homepage

# Force full report regeneration
./deploy_smart.sh reports

# Check deployment status
./deploy_smart.sh status
```

### Homepage-Only Generation

To regenerate just the homepage without all reports:

```bash
python3 generate_homepage_only.py
```

## How It Works

### Auto Mode (Default)
1. Detects changes in files
2. Homepage changes deploy immediately
3. Report changes accumulate until threshold (5 changes) is reached
4. Code changes trigger immediate full deployment

### Change Detection
- Tracks file hashes to detect real changes
- Counts changes since last report deployment
- Separate tracking for homepage vs reports

### Deployment Types

#### Homepage Deploy
- Updates only `index.html`
- No cooldown period
- Instant deployment
- Perfect for quick updates

#### Full Report Deploy
- Regenerates all building reports
- 5-minute cooldown between deploys
- Triggered by:
  - 5+ accumulated changes
  - Code changes
  - Manual request

### State Management

The system maintains state in `deployment_state.json`:
- Change counter
- Last deployment times
- File hashes for change detection
- Deployment history

## Benefits

1. **Faster Updates**: Homepage updates in seconds instead of minutes
2. **Resource Efficient**: Avoids unnecessary report regeneration
3. **No Overlaps**: Lock system prevents concurrent deployments
4. **Smart Triggers**: Only regenerates when needed
5. **Visibility**: Clear status reporting

## Examples

### Scenario 1: Homepage Text Update
```bash
# Edit homepage generation code
# Run smart deploy
./deploy_smart.sh
# Result: Homepage deploys immediately
```

### Scenario 2: Multiple Small Changes
```bash
# Make 3 changes
./deploy_smart.sh  # Shows "2 more changes needed"
# Make 2 more changes
./deploy_smart.sh  # Triggers full report regeneration
```

### Scenario 3: Check Status
```bash
./deploy_smart.sh status
# Output:
# 📊 Deployment Status:
# Changes since last report deploy: 3/5
# Last homepage deploy: 2.5 minutes ago
# Last report deploy: 45.2 minutes ago
```

## Configuration

Edit `deploy_manager.py` to adjust:
- `changes_threshold`: Number of changes before report regen (default: 5)
- `homepage_cooldown`: Seconds between homepage deploys (default: 0)
- `report_cooldown`: Seconds between report deploys (default: 300)

## Troubleshooting

### Deployment Stuck
If a deployment gets stuck, remove the lock file:
```bash
rm deployment.lock
```

### Reset State
To reset deployment tracking:
```bash
rm deployment_state.json
```

### Force Immediate Deploy
To bypass all checks:
```bash
# For reports
bash deploy_reports.sh

# For homepage only
python3 generate_homepage_only.py
git add building_reports/index.html
git commit -m "Homepage update"
git push
```