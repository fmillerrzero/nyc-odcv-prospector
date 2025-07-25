#!/usr/bin/env python3
"""
Intelligent deployment manager for NYC ODCV Prospector
Separates homepage and full report deployments with smart change tracking
"""

import json
import os
import time
import subprocess
from datetime import datetime
from pathlib import Path
import fcntl
import hashlib

class DeploymentManager:
    def __init__(self):
        self.state_file = Path("deployment_state.json")
        self.lock_file = Path("deployment.lock")
        self.changes_threshold = 5  # Number of changes before report regen
        self.homepage_cooldown = 0  # Homepage can deploy immediately
        self.report_cooldown = 300  # 5 minutes between report deploys
        
    def _load_state(self):
        """Load deployment state from file"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "changes_since_last_report_deploy": 0,
            "last_homepage_deploy": 0,
            "last_report_deploy": 0,
            "last_file_hashes": {},
            "deployment_history": []
        }
    
    def _save_state(self, state):
        """Save deployment state to file"""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def _acquire_lock(self):
        """Acquire deployment lock to prevent overlapping deploys"""
        lock_handle = open(self.lock_file, 'w')
        try:
            fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return lock_handle
        except IOError:
            lock_handle.close()
            return None
    
    def _release_lock(self, lock_handle):
        """Release deployment lock"""
        if lock_handle:
            fcntl.flock(lock_handle, fcntl.LOCK_UN)
            lock_handle.close()
            try:
                os.remove(self.lock_file)
            except:
                pass
    
    def _get_file_hash(self, filepath):
        """Get hash of a file for change detection"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def _detect_changes(self, state):
        """Detect what files have changed"""
        changes = {
            "homepage_changed": False,
            "reports_changed": False,
            "code_changed": False,
            "total_changes": 0
        }
        
        # Check main Python file
        py_hash = self._get_file_hash("nyc_odcv_prospector.py")
        if py_hash != state["last_file_hashes"].get("nyc_odcv_prospector.py"):
            changes["code_changed"] = True
            changes["total_changes"] += 1
            state["last_file_hashes"]["nyc_odcv_prospector.py"] = py_hash
        
        # Check if index.html exists and changed
        index_hash = self._get_file_hash("building_reports/index.html")
        if index_hash and index_hash != state["last_file_hashes"].get("index.html"):
            changes["homepage_changed"] = True
            changes["total_changes"] += 1
            state["last_file_hashes"]["index.html"] = index_hash
        
        # Check report files (sample a few)
        report_dir = Path("building_reports")
        if report_dir.exists():
            report_files = list(report_dir.glob("*.html"))
            sample_changed = 0
            for report_file in report_files[:10]:  # Check first 10
                report_hash = self._get_file_hash(str(report_file))
                old_hash = state["last_file_hashes"].get(str(report_file))
                if report_hash != old_hash:
                    sample_changed += 1
                    state["last_file_hashes"][str(report_file)] = report_hash
            
            if sample_changed > 0:
                changes["reports_changed"] = True
                changes["total_changes"] += sample_changed
        
        return changes
    
    def deploy_homepage_only(self):
        """Deploy only the homepage (index.html)"""
        print("🏠 Deploying homepage only...")
        
        # First, generate the homepage
        print("   Generating homepage...")
        try:
            subprocess.run(["python3", "generate_homepage_only.py"], check=True)
        except:
            print("   ⚠️  Homepage generation failed, trying to deploy existing...")
        
        # Add cache-busting to prevent stale content
        print("   Adding cache-busting parameters...")
        try:
            subprocess.run(["python3", "add_cache_busting.py"], check=True)
        except:
            print("   ⚠️  Cache-busting failed, continuing...")
        
        # Git operations for homepage only
        try:
            subprocess.run(["git", "add", "building_reports/index.html"], check=True)
            subprocess.run(["git", "add", "deployment_state.json"], check=False)
            
            # Check if there are actual changes
            result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
            if result.returncode != 0:  # There are changes
                commit_msg = f"Homepage update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                subprocess.run(["git", "commit", "-m", commit_msg], check=True)
                subprocess.run(["git", "push", "origin", "main"], check=True)
                print("✅ Homepage deployed successfully!")
            else:
                print("   No changes to deploy")
        except subprocess.CalledProcessError as e:
            print(f"❌ Deployment failed: {e}")
    
    def deploy_full_reports(self):
        """Deploy all reports (full regeneration)"""
        print("📊 Deploying full reports...")
        
        # Run the existing deploy script
        subprocess.run(["bash", "deploy_reports.sh"], check=True)
        
        print("✅ Full reports deployed successfully!")
    
    def should_deploy(self, deploy_type="auto"):
        """Determine if deployment should proceed"""
        lock = self._acquire_lock()
        if not lock:
            print("❌ Another deployment is in progress. Skipping.")
            return False
        
        try:
            state = self._load_state()
            current_time = time.time()
            
            # Detect changes
            changes = self._detect_changes(state)
            
            # Check cooldowns
            homepage_ready = (current_time - state["last_homepage_deploy"]) > self.homepage_cooldown
            reports_ready = (current_time - state["last_report_deploy"]) > self.report_cooldown
            
            # Deployment logic
            if deploy_type == "homepage":
                if homepage_ready and changes["homepage_changed"]:
                    state["last_homepage_deploy"] = current_time
                    self._save_state(state)
                    self.deploy_homepage_only()
                    return True
                    
            elif deploy_type == "reports":
                if reports_ready:
                    state["changes_since_last_report_deploy"] = 0
                    state["last_report_deploy"] = current_time
                    self._save_state(state)
                    self.deploy_full_reports()
                    return True
                    
            elif deploy_type == "auto":
                # Auto mode: smart deployment based on changes
                state["changes_since_last_report_deploy"] += changes["total_changes"]
                
                # Homepage can deploy immediately if changed
                if changes["homepage_changed"] and homepage_ready:
                    state["last_homepage_deploy"] = current_time
                    self._save_state(state)
                    self.deploy_homepage_only()
                    
                # Check if we need full report deployment
                elif (state["changes_since_last_report_deploy"] >= self.changes_threshold 
                      and reports_ready) or changes["code_changed"]:
                    state["changes_since_last_report_deploy"] = 0
                    state["last_report_deploy"] = current_time
                    self._save_state(state)
                    self.deploy_full_reports()
                else:
                    remaining = self.changes_threshold - state["changes_since_last_report_deploy"]
                    print(f"📊 {remaining} more changes needed before report regeneration")
                    self._save_state(state)
                
                return True
            
            return False
            
        finally:
            self._release_lock(lock)
    
    def status(self):
        """Show deployment status"""
        state = self._load_state()
        current_time = time.time()
        
        print("📊 Deployment Status:")
        print(f"Changes since last report deploy: {state['changes_since_last_report_deploy']}/{self.changes_threshold}")
        
        last_homepage = state.get("last_homepage_deploy", 0)
        if last_homepage:
            mins_ago = (current_time - last_homepage) / 60
            print(f"Last homepage deploy: {mins_ago:.1f} minutes ago")
        
        last_report = state.get("last_report_deploy", 0)
        if last_report:
            mins_ago = (current_time - last_report) / 60
            print(f"Last report deploy: {mins_ago:.1f} minutes ago")
            cooldown_remaining = max(0, self.report_cooldown - (current_time - last_report))
            if cooldown_remaining > 0:
                print(f"Report cooldown: {cooldown_remaining/60:.1f} minutes remaining")


if __name__ == "__main__":
    import sys
    
    manager = DeploymentManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "homepage":
            manager.should_deploy("homepage")
        elif command == "reports":
            manager.should_deploy("reports")
        elif command == "auto":
            manager.should_deploy("auto")
        elif command == "status":
            manager.status()
        else:
            print("Usage: python deploy_manager.py [homepage|reports|auto|status]")
    else:
        # Default to auto mode
        manager.should_deploy("auto")