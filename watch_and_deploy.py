#!/usr/bin/env python3
"""
File watcher that triggers deployments when files change
This provides REAL automatic deployment on file changes
"""

import os
import time
import subprocess
from pathlib import Path
from datetime import datetime
import hashlib
import json

class FileWatcher:
    def __init__(self):
        self.watch_paths = [
            'nyc_odcv_prospector.py',
            'building_reports/index.html',
            'data_for_viz/',
            'final_building_rankings.csv'
        ]
        self.last_hashes = {}
        self.state_file = Path('watcher_state.json')
        self.load_state()
        
    def load_state(self):
        """Load previous file hashes"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                self.last_hashes = json.load(f)
    
    def save_state(self):
        """Save current file hashes"""
        with open(self.state_file, 'w') as f:
            json.dump(self.last_hashes, f)
    
    def get_file_hash(self, filepath):
        """Get hash of file or directory"""
        if not os.path.exists(filepath):
            return None
            
        if os.path.isfile(filepath):
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        elif os.path.isdir(filepath):
            # For directories, hash the list of files
            files = []
            for root, dirs, filenames in os.walk(filepath):
                for filename in filenames:
                    if not filename.startswith('.'):
                        files.append(os.path.join(root, filename))
            return hashlib.md5(','.join(sorted(files)).encode()).hexdigest()
        return None
    
    def check_for_changes(self):
        """Check if any watched files have changed"""
        changes = []
        
        for path in self.watch_paths:
            current_hash = self.get_file_hash(path)
            last_hash = self.last_hashes.get(path)
            
            if current_hash != last_hash:
                changes.append(path)
                self.last_hashes[path] = current_hash
        
        return changes
    
    def run(self):
        """Main watcher loop"""
        print(f"🔍 File watcher started at {datetime.now()}")
        print(f"Watching: {', '.join(self.watch_paths)}")
        
        while True:
            try:
                changes = self.check_for_changes()
                
                if changes:
                    print(f"\n📝 Changes detected at {datetime.now()}:")
                    for change in changes:
                        print(f"  - {change}")
                    
                    # Determine deployment type
                    if 'nyc_odcv_prospector.py' in changes:
                        print("🚀 Code change detected - triggering full deployment...")
                        subprocess.run(['./deploy_smart.sh', 'reports'])
                    elif 'building_reports/index.html' in changes:
                        print("🏠 Homepage change detected - triggering homepage deployment...")
                        subprocess.run(['./deploy_smart.sh', 'homepage'])
                    else:
                        print("🤖 Other changes detected - running auto deployment...")
                        subprocess.run(['./deploy_smart.sh', 'auto'])
                    
                    self.save_state()
                    print(f"✅ Deployment complete at {datetime.now()}")
                
                # Check every 30 seconds
                time.sleep(30)
                
            except KeyboardInterrupt:
                print("\n👋 File watcher stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(60)  # Wait longer on error

if __name__ == "__main__":
    watcher = FileWatcher()
    watcher.run()