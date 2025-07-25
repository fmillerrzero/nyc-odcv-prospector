#!/usr/bin/env python3
"""
Generate only the homepage (index.html) without regenerating all building reports
This is much faster and can be run frequently
"""

import pandas as pd
import os
import json
from collections import defaultdict
from pathlib import Path
import re

# Set up directories
output_dir = 'building_reports'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

print("🏠 Generating homepage only...")

# Load the preprocessed scoring data
try:
    all_buildings = pd.read_csv('final_building_rankings.csv')
    print(f"Loaded {len(all_buildings)} buildings from rankings")
except Exception as e:
    print(f"Error loading rankings: {e}")
    print("Please run the full report generation first")
    exit(1)

# Load additional data sources
data = {}
try:
    # Load necessary data files
    data['energy'] = pd.read_csv('data_for_viz/energy_BIG.csv')
    data['emissions'] = pd.read_csv('data_for_viz/emissions_BIG.csv')
    data['addresses'] = pd.read_csv('data_for_viz/addresses_BIG.csv')
    data['penalties'] = pd.read_csv('data_for_viz/penalty_BIG.csv')
    data['system'] = pd.read_csv('data_for_viz/system_BIG.csv')
    data['occupancy_rates'] = pd.read_csv('data_for_viz/neighborhood_occupancy_rates.csv')
    
    # Convert to dictionaries for faster lookup
    for key in ['energy', 'emissions', 'addresses', 'penalties', 'system']:
        if 'bbl' in data[key].columns:
            data[key] = data[key].set_index('bbl').to_dict('index')
except Exception as e:
    print(f"Error loading data files: {e}")
    exit(1)

# Helper functions from main script
def safe_val(data_dict, bbl, key, default='N/A'):
    """Safely get value from data dictionary"""
    try:
        if bbl in data_dict and key in data_dict[bbl]:
            val = data_dict[bbl][key]
            if pd.notna(val):
                return val
        return default
    except:
        return default

def get_neighborhood_occupancy(address):
    """Get occupancy rate for address neighborhood"""
    try:
        if isinstance(data.get('occupancy_rates'), pd.DataFrame):
            for _, row in data['occupancy_rates'].iterrows():
                if row['neighborhood'].lower() in address.lower():
                    return {
                        'rate': row['occupancy_rate'],
                        'trend': row['occupancy_trend'],
                        'neighborhood': row['neighborhood']
                    }
        return {'rate': 88, 'trend': 'stable', 'neighborhood': 'NYC Average'}
    except:
        return {'rate': 88, 'trend': 'stable', 'neighborhood': 'NYC Average'}

def get_occupancy_adjusted_savings(base_savings, occupancy_data, has_bas):
    """Calculate occupancy-adjusted ODCV savings"""
    if isinstance(occupancy_data, dict):
        occ_rate = occupancy_data['rate']
    else:
        occ_rate = occupancy_data
    
    # Higher adjustment for low occupancy
    if occ_rate < 70:
        multiplier = 1.5 if has_bas == 'yes' else 1.8
    elif occ_rate < 80:
        multiplier = 1.3 if has_bas == 'yes' else 1.5
    elif occ_rate < 85:
        multiplier = 1.1 if has_bas == 'yes' else 1.2
    else:
        multiplier = 1.0
    
    return base_savings * multiplier

def format_currency(value):
    """Format currency values"""
    if value >= 1000000:
        return f"${value/1000000:.1f}M"
    elif value >= 1000:
        return f"${value/1000:.0f}K"
    else:
        return f"${value:.0f}"

def find_logo_file(owner_name):
    """Find logo file for owner"""
    logos_dir = Path('Logos')
    if not logos_dir.exists():
        return None
    
    # Clean owner name
    clean_name = owner_name.replace(' ', '_').replace('&', 'and')
    
    # Try exact match first
    for ext in ['.png', '.jpg', '.jpeg', '.svg']:
        logo_path = logos_dir / f"{clean_name}{ext}"
        if logo_path.exists():
            return logo_path.name
    
    # Try partial match
    for logo_file in logos_dir.iterdir():
        if clean_name.lower() in logo_file.stem.lower():
            return logo_file.name
    
    return None

# Collect homepage data
homepage_data = []
for idx, row in all_buildings.iterrows():
    bbl = int(row['bbl'])
    
    # Get building details
    main_address = safe_val(data['addresses'], bbl, 'main_address', f'Building {bbl}')
    safe_address = main_address.replace('/', '-').replace('\\', '-').replace(':', '-')
    
    # Get occupancy-adjusted savings
    base_savings = float(row.get('Total_ODCV_Savings_Annual_USD', 0))
    building_bas = safe_val(data['system'], bbl, 'Has Building Automation', 'N/A')
    occupancy_data = get_neighborhood_occupancy(main_address)
    adjusted_savings = get_occupancy_adjusted_savings(base_savings, occupancy_data, building_bas)
    
    homepage_data.append({
        'bbl': bbl,
        'rank': int(row['final_rank']),
        'address': main_address,
        'filename': f"{bbl}_{safe_address}.html",
        'owner': row.get('portfolio_owner', 'Unknown'),
        'savings': adjusted_savings,
        'bas': building_bas.lower() if building_bas != 'N/A' else 'unknown',
        'penalty_2026': float(safe_val(data['penalties'], bbl, 'estimated_penalty_2026', 0)),
        'score': float(row.get('total_score', 0)),
        'search_text': f"{main_address} {row.get('portfolio_owner', '')} {row.get('property_manager', '')}".lower(),
        'occupancy_rate': occupancy_data['rate'] if isinstance(occupancy_data, dict) else occupancy_data,
        'occupancy_trend': occupancy_data.get('trend', 'stable') if isinstance(occupancy_data, dict) else 'stable',
        'neighborhood': occupancy_data.get('neighborhood', 'Unknown') if isinstance(occupancy_data, dict) else 'Unknown'
    })

# Calculate stats
total_savings = sum(b['savings'] for b in homepage_data)
bas_yes = sum(1 for b in homepage_data if b['bas'] == 'yes')
urgent = sum(1 for b in homepage_data if b['penalty_2026'] > 0)
total_penalties = sum(b['penalty_2026'] for b in homepage_data if b['penalty_2026'] > 0)

# Portfolio stats
portfolio_stats = defaultdict(lambda: {'count': 0, 'total': 0})
for b in homepage_data:
    portfolio_stats[b['owner']]['count'] += 1
    portfolio_stats[b['owner']]['total'] += b['savings']

top_portfolios = sorted(
    [(owner, stats) for owner, stats in portfolio_stats.items()],
    key=lambda x: x[1]['total'],
    reverse=True
)[:3]

# Add logos
for i, (owner, stats) in enumerate(top_portfolios):
    owner_logo = find_logo_file(owner)
    top_portfolios[i] = (owner, stats, owner_logo)

# Generate homepage HTML (rest of the template remains the same)
homepage_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>NYC ODCV Opportunity Rankings | R-Zero</title>
    <style>
        :root {{
            --rzero-primary: #00769d;
            --rzero-secondary: #e3f2f7;
            --rzero-accent: #ff6b35;
            --rzero-success: #4CAF50;
            --rzero-warning: #ff9800;
            --rzero-danger: #f44336;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f6fa;
            color: #333;
        }}
        
        .header {{
            background: linear-gradient(135deg, #00769d 0%, #005a7d 100%);
            color: white;
            padding: 30px 40px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        /* Quick stats styling */
        .quick-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border: 1px solid #e0e0e0;
            transition: transform 0.2s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }}
        
        /* Filter buttons */
        .filter-container {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        .filter-btn {{
            background: #f0f0f0;
            border: 1px solid #ddd;
            padding: 10px 20px;
            margin: 5px;
            border-radius: 25px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
        }}
        
        .filter-btn:hover {{
            background: var(--rzero-secondary);
            border-color: var(--rzero-primary);
        }}
        
        .filter-btn.active {{
            background: var(--rzero-primary);
            color: white;
            border-color: var(--rzero-primary);
        }}
        
        /* Table styling */
        table {{
            width: 100%;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        th {{
            background: #f8f9fa;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        td {{
            padding: 15px;
            border-bottom: 1px solid #f0f0f0;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .clickable-row {{
            cursor: pointer;
            transition: background 0.2s;
        }}
        
        .thumb-cell img {{
            width: 120px;
            height: 80px;
            object-fit: cover;
            border-radius: 8px;
        }}
        
        /* Portfolio tiles */
        .portfolio-tile {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid rgba(0, 118, 157, 0.2);
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            min-height: 100px;
        }}
        
        .portfolio-tile:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,118,157,0.2);
            border-color: var(--rzero-primary);
        }}
        
        /* Search box */
        .search-box {{
            width: 100%;
            padding: 15px;
            font-size: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            transition: border-color 0.3s;
        }}
        
        .search-box:focus {{
            outline: none;
            border-color: var(--rzero-primary);
        }}
    </style>
</head>
<body>
    <div class="header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h1 style="margin: 0 0 10px 0; font-size: 2.5em;">NYC ODCV Opportunity Rankings</h1>
                <p style="margin: 0; opacity: 0.9; font-size: 1.1em;">
                    Comprehensive analysis of {len(homepage_data):,} Manhattan office buildings
                </p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 2em; font-weight: bold;">{format_currency(total_savings)}</div>
                <div style="opacity: 0.9;">Total Annual ODCV Savings Potential</div>
            </div>
        </div>
    </div>
    
    <div class="container">
        <!-- Quick Stats -->
        <div class="quick-stats">
            <div class="stat-card">
                <h3>🏢 Buildings with BAS</h3>
                <div style="font-size: 2em; color: var(--rzero-primary);">{bas_yes}</div>
                <div style="color: #666;">Ready for ODCV optimization</div>
            </div>
            
            <div class="stat-card">
                <h3>⚠️ Urgent Action Needed</h3>
                <div style="font-size: 2em; color: var(--rzero-danger);">{urgent}</div>
                <div style="color: #666;">Buildings facing 2026 penalties</div>
            </div>
            
            <div class="stat-card">
                <h3>💰 Penalty Exposure</h3>
                <div style="font-size: 2em; color: var(--rzero-warning);">{format_currency(total_penalties)}</div>
                <div style="color: #666;">Total 2026 penalty risk</div>
            </div>
        </div>
        
        <!-- Top Portfolios -->
        <div class="portfolio-box" style="background: white; padding: 25px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">
            <h2>Top Portfolios</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">
"""

for owner, stats, logo in top_portfolios:
    logo_style = "position: absolute; top: 10px; right: 15px; max-height: 60px; max-width: 120px; opacity: 0.8;" if "Vornado" in owner else "position: absolute; top: 15px; right: 15px; max-height: 40px; max-width: 80px; opacity: 0.8;"
    
    homepage_html += f"""
                <div class="portfolio-tile" onclick="filterByOwner('{owner.replace("'", "\\'")}')" style="background: #f8f9fa; padding: 20px; border-radius: 8px; border: 1px solid rgba(0, 118, 157, 0.2); cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; min-height: 100px;">
                    {f'<img src="https://raw.githubusercontent.com/fmillerrzero/nyc-odcv-prospector/main/Logos/{logo}" alt="{owner}" style="{logo_style}">' if logo else ''}
                    <strong style="color: var(--rzero-primary); display: block; margin-bottom: 5px;">{owner}</strong>
                    <span style="color: #666;">{stats['count']} buildings • ${stats['total']/1000000:.1f}M savings</span>
                </div>
    """

homepage_html += """
            </div>
        </div>
        
        <!-- Filter Section -->
        <div class="filter-container">
            <div style="margin-bottom: 10px;">
                <strong>Quick Filters:</strong>
                <span id="resultCount" style="float: right; color: #666;"></span>
            </div>
            <div>
                <button class="filter-btn" onclick="filterBAS('yes')">🏢 Has BAS</button>
                <button class="filter-btn" onclick="filterPenalties()">⚠️ 2026 Penalties</button>
                <button class="filter-btn" onclick="filterTop50()">🏆 Top 50</button>
                <button class="filter-btn" onclick="filterHighSavings()">💰 $500K+ Savings</button>
                <button class="filter-btn" onclick="filterLowOccupancy()">📉 Low Occupancy</button>
                <button id="clearFilterBtn" onclick="clearAllFilters()" style="background: #e0e0e0; color: #999; border: none; padding: 10px 20px; margin: 5px; border-radius: 25px; cursor: not-allowed; font-size: 14px;" disabled>Clear Filters</button>
            </div>
        </div>
        
        <!-- Search and Export -->
        <div style="display: flex; gap: 10px; margin-bottom: 20px;">
            <input type="text" class="search-box" id="search" placeholder="Search by address, owner, property manager" onkeyup="filterTable()">
            <button onclick="exportResults()" style="background: var(--rzero-primary); color: white; border: none; padding: 15px 25px; border-radius: 8px; cursor: pointer; font-size: 16px; white-space: nowrap;">
                📥 Export Results
            </button>
        </div>
        
        <!-- Results Table -->
        <table>
            <thead>
                <tr>
                    <th>Building</th>
                    <th>Rank</th>
                    <th>Address</th>
                    <th>Owner</th>
                    <th>Annual ODCV Savings</th>
                    <th>BAS</th>
                    <th>2026 Penalty</th>
                    <th>Score</th>
                    <th>Occupancy</th>
                </tr>
            </thead>
            <tbody id="buildingTable">
"""

# Add table rows
for b in homepage_data:
    bas_class = 'yes' if b['bas'] == 'yes' else 'no' if b['bas'] == 'no' else ''
    penalty_class = 'urgent' if b['penalty_2026'] > 0 else ''
    
    # Thumbnail
    thumb_path = f"hero_thumbnails/{b['bbl']}_thumbnail.jpg"
    thumb_cell = f'<img src="{thumb_path}" alt="{b["address"]}" onerror="this.src=\'https://via.placeholder.com/120x80?text=No+Image\'">' if os.path.exists(f"hero_thumbnails/{b['bbl']}_thumbnail.jpg") else '<img src="https://via.placeholder.com/120x80?text=No+Image" alt="No thumbnail">'
    
    # Occupancy indicator
    occ_rate = b['occupancy_rate']
    if occ_rate < 70:
        occ_color = '#f44336'
        occ_emoji = '🔴'
    elif occ_rate < 80:
        occ_color = '#ff9800'
        occ_emoji = '🟡'
    else:
        occ_color = '#4CAF50'
        occ_emoji = '🟢'
    
    homepage_html += f"""
                <tr data-search="{b['search_text']}" data-occupancy="{occ_rate}" class="clickable-row" onclick="if (!event.target.closest('a')) window.location.href='{b['filename']}'">
                    <td class="thumb-cell">{thumb_cell}</td>
                    <td><span style="font-weight: bold; color: var(--rzero-primary);">#{b['rank']}</span></td>
                    <td>{b['address']}</td>
                    <td>{b['owner']}</td>
                    <td style="font-weight: bold; color: #2e7d32;">{format_currency(b['savings'])}</td>
                    <td class="{bas_class}">{'✅' if b['bas'] == 'yes' else '❌' if b['bas'] == 'no' else '❓'}</td>
                    <td class="{penalty_class}" style="color: {'#d32f2f' if b['penalty_2026'] > 0 else '#999'};">
                        {format_currency(b['penalty_2026']) if b['penalty_2026'] > 0 else '-'}
                    </td>
                    <td>{b['score']:.1f}</td>
                    <td>
                        <span style="color: {occ_color};">
                            {occ_emoji} {occ_rate}%
                        </span>
                    </td>
                </tr>
    """

homepage_html += """
            </tbody>
        </table>
    </div>
    
    <script>
        let activeFilters = [];
        
        function updateResultCount() {
            const table = document.getElementById('buildingTable');
            const visibleRows = Array.from(table.getElementsByTagName('tr')).filter(row => row.style.display !== 'none');
            document.getElementById('resultCount').textContent = `Showing ${visibleRows.length} buildings`;
        }
        
        function filterTable() {
            const input = document.getElementById('search');
            const filter = input.value.toLowerCase();
            const table = document.getElementById('buildingTable');
            const rows = table.getElementsByTagName('tr');
            
            for (let row of rows) {
                const searchText = row.getAttribute('data-search');
                if (searchText && searchText.includes(filter)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            }
            updateResultCount();
        }
        
        function filterBAS(value) {
            toggleFilter('bas', value);
            applyFilters();
        }
        
        function filterPenalties() {
            toggleFilter('penalty', true);
            applyFilters();
        }
        
        function filterTop50() {
            toggleFilter('top50', true);
            applyFilters();
        }
        
        function filterHighSavings() {
            toggleFilter('highsavings', true);
            applyFilters();
        }
        
        function filterLowOccupancy() {
            toggleFilter('lowoccupancy', true);
            applyFilters();
        }
        
        function filterByOwner(owner) {
            const searchBox = document.getElementById('search');
            searchBox.value = owner;
            filterTable();
        }
        
        function toggleFilter(type, value) {
            const existingIndex = activeFilters.findIndex(f => f.type === type);
            if (existingIndex >= 0) {
                activeFilters.splice(existingIndex, 1);
            } else {
                activeFilters.push({type, value});
            }
            
            // Update button states
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            activeFilters.forEach(filter => {
                let selector;
                switch(filter.type) {
                    case 'bas': selector = "button[onclick*='filterBAS']"; break;
                    case 'penalty': selector = "button[onclick*='filterPenalties']"; break;
                    case 'top50': selector = "button[onclick*='filterTop50']"; break;
                    case 'highsavings': selector = "button[onclick*='filterHighSavings']"; break;
                    case 'lowoccupancy': selector = "button[onclick*='filterLowOccupancy']"; break;
                }
                if (selector) {
                    const btn = document.querySelector(selector);
                    if (btn) btn.classList.add('active');
                }
            });
            
            // Enable/disable clear button
            const clearBtn = document.getElementById('clearFilterBtn');
            if (activeFilters.length > 0) {
                clearBtn.disabled = false;
                clearBtn.style.cursor = 'pointer';
                clearBtn.style.background = '#f44336';
                clearBtn.style.color = 'white';
            } else {
                clearBtn.disabled = true;
                clearBtn.style.cursor = 'not-allowed';
                clearBtn.style.background = '#e0e0e0';
                clearBtn.style.color = '#999';
            }
        }
        
        function applyFilters() {
            const table = document.getElementById('buildingTable');
            const rows = table.getElementsByTagName('tr');
            
            for (let i = 0; i < rows.length; i++) {
                const row = rows[i];
                let show = true;
                
                for (let filter of activeFilters) {
                    switch(filter.type) {
                        case 'bas':
                            const basCell = row.cells[5];
                            if (!basCell || !basCell.textContent.includes('✅')) show = false;
                            break;
                        case 'penalty':
                            const penaltyCell = row.cells[6];
                            if (!penaltyCell || penaltyCell.textContent === '-') show = false;
                            break;
                        case 'top50':
                            const rankCell = row.cells[1];
                            const rank = parseInt(rankCell.textContent.replace('#', ''));
                            if (rank > 50) show = false;
                            break;
                        case 'highsavings':
                            const savingsCell = row.cells[4];
                            const savingsText = savingsCell.textContent;
                            if (savingsText.includes('M')) {
                                // Million dollar savings always qualify
                            } else if (savingsText.includes('K')) {
                                const amount = parseFloat(savingsText.replace('$', '').replace('K', ''));
                                if (amount < 500) show = false;
                            } else {
                                show = false;
                            }
                            break;
                        case 'lowoccupancy':
                            const occRate = parseFloat(row.getAttribute('data-occupancy'));
                            if (occRate >= 80) show = false;
                            break;
                    }
                }
                
                row.style.display = show ? '' : 'none';
            }
            
            updateResultCount();
        }
        
        function clearAllFilters() {
            activeFilters = [];
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            const clearBtn = document.getElementById('clearFilterBtn');
            clearBtn.disabled = true;
            clearBtn.style.cursor = 'not-allowed';
            clearBtn.style.background = '#e0e0e0';
            clearBtn.style.color = '#999';
            
            // Clear search too
            document.getElementById('search').value = '';
            
            // Show all rows
            const table = document.getElementById('buildingTable');
            const rows = table.getElementsByTagName('tr');
            for (let row of rows) {
                row.style.display = '';
            }
            
            updateResultCount();
        }
        
        function exportResults() {
            const table = document.getElementById('buildingTable');
            const rows = Array.from(table.getElementsByTagName('tr')).filter(row => row.style.display !== 'none');
            
            let csv = 'Rank,Address,Owner,Annual ODCV Savings,BAS,2026 Penalty,Score,Occupancy\\n';
            
            rows.forEach(row => {
                const cells = row.cells;
                const rank = cells[1].textContent.replace('#', '');
                const address = cells[2].textContent;
                const owner = cells[3].textContent;
                const savings = cells[4].textContent;
                const bas = cells[5].textContent.includes('✅') ? 'Yes' : cells[5].textContent.includes('❌') ? 'No' : 'Unknown';
                const penalty = cells[6].textContent;
                const score = cells[7].textContent;
                const occupancy = cells[8].textContent.replace(/[🔴🟡🟢]/g, '').trim();
                
                csv += `"${rank}","${address}","${owner}","${savings}","${bas}","${penalty}","${score}","${occupancy}"\\n`;
            });
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'nyc_odcv_opportunities.csv';
            a.click();
            window.URL.revokeObjectURL(url);
        }
        
        // Initialize
        updateResultCount();
    </script>
</body>
</html>
"""

# Save homepage
with open(os.path.join(output_dir, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(homepage_html)

print("✅ Homepage generated successfully!")
print(f"   Location: {os.path.join(output_dir, 'index.html')}")
print(f"   Buildings: {len(homepage_data)}")
print(f"   Total savings: {format_currency(total_savings)}")