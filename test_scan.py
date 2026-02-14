#!/usr/bin/env python3
"""
Test script to run a complete scan of inheritans.com and verify all tools work correctly
"""
import requests
import time
import json

API_BASE = "http://localhost:5000/api"
TARGET = "inheritans.com"

def create_scan():
    """Create a new scan"""
    print(f"\n{'='*60}")
    print(f"Creating new scan for {TARGET}")
    print(f"{'='*60}\n")
    
    response = requests.post(f"{API_BASE}/target", json={
        "domain": TARGET,
        "rate_limit": 150
    })
    
    if response.status_code == 200:
        data = response.json()
        scan_id = data['scan_id']
        print(f"✓ Scan created: {scan_id}\n")
        return scan_id
    else:
        print(f"✗ Failed to create scan: {response.text}")
        return None

def start_auto_scan(scan_id):
    """Start auto scan"""
    print(f"Starting auto scan...")
    response = requests.post(f"{API_BASE}/scan/{scan_id}/auto")
    
    if response.status_code == 200:
        print(f"✓ Auto scan started\n")
        return True
    else:
        print(f"✗ Failed to start auto scan: {response.text}")
        return False

def monitor_scan(scan_id):
    """Monitor scan progress"""
    print(f"Monitoring scan progress...\n")
    
    tools = ['subfinder', 'findomain', 'assetfinder', 'sublist3r', 'crtsh', 
             'merge', 'dnsx', 'httpx', 'gau', 'gospider', 'merge2', 'gowitness']
    
    completed_tools = set()
    last_status = {}
    
    while True:
        try:
            response = requests.get(f"{API_BASE}/scan/{scan_id}/tools")
            if response.status_code == 200:
                data = response.json()
                tools_status = data['tools']
                
                # Check for changes
                for tool_name in tools:
                    if tool_name in tools_status:
                        tool = tools_status[tool_name]
                        status = tool['status']
                        count = tool['count']
                        
                        # Print status changes
                        if tool_name not in last_status or last_status[tool_name] != (status, count):
                            last_status[tool_name] = (status, count)
                            
                            if status == 'running':
                                print(f"⏳ {tool_name.upper():<12} - Running...")
                            elif status == 'completed':
                                if tool_name not in completed_tools:
                                    print(f"✓  {tool_name.upper():<12} - Completed ({count} results)")
                                    completed_tools.add(tool_name)
                            elif status == 'failed':
                                print(f"✗  {tool_name.upper():<12} - Failed")
                                completed_tools.add(tool_name)
                
                # Check if all tools are done
                all_done = all(
                    tools_status.get(t, {}).get('status') in ['completed', 'failed', 'idle']
                    for t in tools
                )
                
                # Check if the last tool (gowitness) is done
                if tools_status.get('gowitness', {}).get('status') == 'completed':
                    print(f"\n{'='*60}")
                    print(f"Scan completed!")
                    print(f"{'='*60}\n")
                    return tools_status
                
            time.sleep(3)
            
        except KeyboardInterrupt:
            print("\n\nScan monitoring stopped by user")
            return None
        except Exception as e:
            print(f"Error monitoring scan: {e}")
            time.sleep(5)

def get_results(scan_id):
    """Get scan results"""
    print(f"\nFetching results...\n")
    
    # Get subdomains
    response = requests.get(f"{API_BASE}/scan/{scan_id}/subdomains")
    if response.status_code == 200:
        subdomains = response.json()['subdomains']
        print(f"Subdomains: {len(subdomains)}")
        for sd in subdomains[:5]:
            print(f"  - {sd}")
        if len(subdomains) > 5:
            print(f"  ... and {len(subdomains) - 5} more")
    
    # Get URLs
    response = requests.get(f"{API_BASE}/scan/{scan_id}/urls")
    if response.status_code == 200:
        urls = response.json()['urls']
        print(f"\nURLs: {len(urls)}")
        for url_data in urls[:5]:
            print(f"  - {url_data['url']} ({url_data.get('status_code', 'N/A')})")
        if len(urls) > 5:
            print(f"  ... and {len(urls) - 5} more")
    
    # Get screenshots
    response = requests.get(f"{API_BASE}/scan/{scan_id}/screenshots")
    if response.status_code == 200:
        screenshots = response.json()['screenshots']
        print(f"\nScreenshots: {len(screenshots)}")
        for shot in screenshots[:5]:
            print(f"  - {shot['url']} ({shot.get('status_code', 'N/A')})")
        if len(screenshots) > 5:
            print(f"  ... and {len(screenshots) - 5} more")

def main():
    print(f"\n{'#'*60}")
    print(f"# DomScout v2 - Test Scan Script")
    print(f"# Target: {TARGET}")
    print(f"{'#'*60}")
    
    # Create scan
    scan_id = create_scan()
    if not scan_id:
        return
    
    # Start auto scan
    if not start_auto_scan(scan_id):
        return
    
    # Monitor progress
    final_status = monitor_scan(scan_id)
    
    if final_status:
        # Get and display results
        get_results(scan_id)
        
        print(f"\n{'='*60}")
        print(f"Scan ID: {scan_id}")
        print(f"View results at: http://localhost:5000/results/{scan_id}")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
