#!/usr/bin/env python3
"""
Add cache-busting query parameters to all links in HTML files
"""

import os
import re
from datetime import datetime
from pathlib import Path

def add_cache_busting_to_html(html_content, timestamp=None):
    """Add cache-busting query parameters to CSS, JS, and image links"""
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    # Add cache busting to CSS links
    html_content = re.sub(
        r'(href="[^"]+\.css)(")',
        f'\\1?v={timestamp}\\2',
        html_content
    )
    
    # Add cache busting to JS links
    html_content = re.sub(
        r'(src="[^"]+\.js)(")',
        f'\\1?v={timestamp}\\2',
        html_content
    )
    
    # Add cache busting to image links (jpg, png, etc)
    html_content = re.sub(
        r'(src="[^"]+\.(jpg|jpeg|png|gif|webp))(")',
        f'\\1?v={timestamp}\\3',
        html_content
    )
    
    return html_content

def process_building_reports():
    """Process all HTML files in building_reports directory"""
    reports_dir = Path("building_reports")
    if not reports_dir.exists():
        print("❌ building_reports directory not found")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    processed = 0
    
    for html_file in reports_dir.glob("*.html"):
        try:
            # Read file
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Add cache busting
            updated_content = add_cache_busting_to_html(content, timestamp)
            
            # Write back only if changed
            if content != updated_content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                processed += 1
                if processed <= 10:
                    print(f"✅ Updated: {html_file.name}")
        except Exception as e:
            print(f"❌ Error processing {html_file.name}: {e}")
    
    print(f"\n📊 Processed {processed} files with cache-busting timestamps")

if __name__ == "__main__":
    print("🔄 Adding cache-busting parameters to HTML files...")
    process_building_reports()