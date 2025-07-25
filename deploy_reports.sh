#!/bin/bash

echo "🟢 FULLY AUTOMATIC deployment starting (100% automatic, no manual input)..."

# Step 1: Clear old reports IN THE GIT REPO
rm -rf "/Users/forrestmiller/Desktop/nyc-odcv-prospector/building_reports/"
mkdir "/Users/forrestmiller/Desktop/nyc-odcv-prospector/building_reports/"

echo "🟢 Old reports cleared successfully."

# Step 2: Generate fresh reports directly in git repo
cd "/Users/forrestmiller/Desktop/nyc-odcv-prospector"
python3 nyc_odcv_prospector.py

echo "🟢 Fresh reports regenerated successfully."

# Step 3: Automatically commit and push everything to GitHub (triggers Render deployment automatically)
git add .
git commit -m "FULLY AUTOMATED deployment: regenerated all reports fresh"
git push origin main

echo "🟢 All reports deployed to GitHub, triggering automatic Render.com deployment!"