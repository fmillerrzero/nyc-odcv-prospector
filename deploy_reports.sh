#!/bin/bash

echo "🟢 FULLY AUTOMATIC deployment starting (100% automatic, no manual input)..."

# Step 1: Fully clear out old reports
rm -rf "/Users/forrestmiller/Desktop/building_reports/"
mkdir "/Users/forrestmiller/Desktop/building_reports/"

echo "🟢 Old reports cleared successfully."

# Step 2: Generate fresh reports from scratch
cd "/Users/forrestmiller/Desktop/nyc-odcv-prospector"
python3 nyc_odcv_prospector.py

echo "🟢 Fresh reports regenerated successfully."

# Step 2.5: Copy generated reports to git repository
cp -r "/Users/forrestmiller/Desktop/building_reports/"* "/Users/forrestmiller/Desktop/nyc-odcv-prospector/building_reports/"

echo "🟢 Reports copied to git repository."

# Step 3: Automatically commit and push everything to GitHub (triggers Render deployment automatically)
git add .
git commit -m "FULLY AUTOMATED deployment: regenerated all reports fresh"
git push origin main

echo "🟢 All reports deployed to GitHub, triggering automatic Render.com deployment!"