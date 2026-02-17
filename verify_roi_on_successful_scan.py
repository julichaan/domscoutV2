#!/usr/bin/env python3
"""
Direct test of ROI calculation on previous successful scan
"""
import sqlite3
import json
import os
import sys
sys.path.insert(0, '/home/kali/Documents/domscoutV2')

from scanner import DomScoutScanner

# Use the scan ID from the successful test
scan_id = "2c9ec3ce-5e10-4af3-8af2-accf6c18a997"
scan_dir = f"/home/kali/Documents/domscoutV2/scan_{scan_id}"

print("[*] Testing ROI Scoring on successful scan")
print(f"[*] Scan ID: {scan_id}")
print("=" * 70)

# Create scanner instance
scanner = DomScoutScanner(
    scan_id,
    'inheritans.com',
    150,
    '/home/kali/Documents/domscoutV2/resolvers.txt',
    '/home/kali/Documents/domscoutV2/screenshots'
)

# Check if gowitness database exists
gowitness_db = os.path.join(scan_dir, "gowitness.sqlite3")
if os.path.exists(gowitness_db):
    print(f"\n[+] GoWitness database found: {gowitness_db}")
    
    # Query database
    try:
        conn = sqlite3.connect(gowitness_db)
        cursor = conn.cursor()
        count = cursor.execute('SELECT COUNT(*) FROM results WHERE filename IS NOT NULL').fetchone()[0]
        print(f"[+] Database has {count} screenshot records")
        
        # Show first few records
        rows = cursor.execute('SELECT url, final_url, response_code, title FROM results LIMIT 5').fetchall()
        print(f"\n[*] First 5 URLs in database:")
        for i, row in enumerate(rows, 1):
            print(f"    {i}. {row[1] or row[0]} (Status: {row[2]})")
        
        conn.close()
    except Exception as e:
        print(f"[!] Error querying database: {e}")
else:
    print(f"[!] GoWitness database not found at {gowitness_db}")
    print(f"[*] Available files in {scan_dir}:")
    if os.path.exists(scan_dir):
        files = os.listdir(scan_dir)
        for f in sorted(files)[:20]:
            print(f"    - {f}")

# Check if scored results file exists
scored_file = os.path.join(scan_dir, 'gowitness_scored_results.json')
if os.path.exists(scored_file):
    print(f"\n[+] Scored results file found: {scored_file}")
    with open(scored_file, 'r') as f:
        data = json.load(f)
        print(f"[+] Total scored URLs: {len(data)}")
        print(f"\n[*] Top 10 URLs by ROI Score (HIGH to LOW):")
        print("=" * 70)
        
        # Sort by score descending
        sorted_data = sorted(data, key=lambda x: -x.get('roi_score', 0))
        
        for i, item in enumerate(sorted_data[:10], 1):
            url = item['url'][:60] if len(item['url']) > 60 else item['url']
            score = item['roi_score']
            print(f"{i:2d}. [{score:3d}] {url}")
        
        if len(sorted_data) > 10:
            print(f"\n    ... and {len(sorted_data) - 10} more URLs")
else:
    print(f"\n[!] Scored results file not found at {scored_file}")
    print("[*] Running ROI calculation now...")
    
    # Calculate ROI for all URLs manually
    gowitness_db = os.path.join(scan_dir, "gowitness.sqlite3")
    if os.path.exists(gowitness_db):
        try:
            conn = sqlite3.connect(gowitness_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            rows = cursor.execute(
                'SELECT url, final_url, response_code, response_reason, title, filename FROM results WHERE filename IS NOT NULL'
            ).fetchall()
            
            print(f"[+] Processing {len(rows)} URLs for ROI scoring...")
            
            scored_results = []
            for row in rows:
                url = row['final_url'] or row['url']
                status_code = row['response_code'] or 200
                
                # Create basic metadata
                metadata = {
                    'url': url,
                    'status_code': status_code,
                    'headers': {},
                    'technologies': [],
                    'endpoints_count': 0,
                    'fuzz_endpoints': 0,
                    'content_length': 0,
                }
                
                # Calculate ROI
                roi_score = scanner.calculate_roi_score(metadata)
                
                scored_results.append({
                    'url': url,
                    'status_code': status_code,
                    'roi_score': roi_score
                })
            
            # Sort by score
            scored_results.sort(key=lambda x: -x['roi_score'])
            
            print(f"\n[*] Top 10 URLs by ROI Score:")
            print("=" * 70)
            for i, item in enumerate(scored_results[:10], 1):
                url = item['url'][:60] if len(item['url']) > 60 else item['url']
                score = item['roi_score']
                print(f"{i:2d}. [{score:3d}] {url}")
            
            conn.close()
            
        except Exception as e:
            print(f"[!] Error: {e}")
            import traceback
            traceback.print_exc()

print("\n" + "=" * 70)
print("[✓] ROI scoring test completed!")
