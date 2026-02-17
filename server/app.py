#!/usr/bin/env python3
import os
import json
import time
import threading
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import subprocess
import uuid
import shutil

# Import domscout functionality
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scanner import DomScoutScanner

app = Flask(__name__, static_folder='static')
CORS(app)

# Database configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'domscout.db')
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'screenshots')
RESOLVERS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resolvers.txt')
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')
SUBFINDER_CONFIG_PATH = os.path.expanduser('~/.config/subfinder/provider-config.yaml')

# Ensure directories exist
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# 50 legitimate user agents for rotation
USER_AGENTS = [
    # Chrome - Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    # Chrome - macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    # Chrome - Linux
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    # Firefox - Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    # Firefox - macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13.6; rv:121.0) Gecko/20100101 Firefox/121.0',
    # Firefox - Linux
    'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
    # Safari - macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15',
    # Safari - iOS
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    # Edge - Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.0.0',
    # Chrome Mobile - Android
    'Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    # Firefox Mobile - Android
    'Mozilla/5.0 (Android 13; Mobile; rv:121.0) Gecko/121.0 Firefox/121.0',
    'Mozilla/5.0 (Android 12; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0',
    # Opera
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0',
    # Brave
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Brave/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Brave/120.0.0.0',
    # Vivaldi
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Vivaldi/6.5.3206.53',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Vivaldi/6.5.3206.53',
    # Additional Chrome versions
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
]

# Global scan tracking
active_scans = {}


def init_db():
    """Initialize the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Scans table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            duration INTEGER,
            rate_limit INTEGER
        )
    ''')
    
    # Subdomains table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subdomains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT NOT NULL,
            subdomain TEXT NOT NULL,
            FOREIGN KEY (scan_id) REFERENCES scans(id)
        )
    ''')
    
    # URLs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT NOT NULL,
            url TEXT NOT NULL,
            status_code INTEGER,
            FOREIGN KEY (scan_id) REFERENCES scans(id)
        )
    ''')
    
    # Screenshots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS screenshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id TEXT NOT NULL,
            url TEXT NOT NULL,
            filename TEXT NOT NULL,
            status_code INTEGER,
            title TEXT,
            headers TEXT,
            roi_score INTEGER DEFAULT 50,
            FOREIGN KEY (scan_id) REFERENCES scans(id)
        )
    ''')
    
    conn.commit()
    conn.close()


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Serve the Vue.js frontend"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files or index.html for SPA routes"""
    # Try to serve the file if it exists
    static_file = os.path.join(app.static_folder, path)
    if os.path.exists(static_file) and os.path.isfile(static_file):
        return send_from_directory(app.static_folder, path)
    # Otherwise serve index.html for Vue Router
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/target', methods=['POST'])
def create_target():
    """Create a new target without starting scan"""
    data = request.json
    domain = data.get('domain')
    rate_limit = data.get('rate_limit', 150)
    
    if not domain:
        return jsonify({'error': 'Domain is required'}), 400
    
    # Generate unique scan ID
    scan_id = str(uuid.uuid4())
    
    # Create scan record with 'created' status
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO scans (id, domain, status, rate_limit) VALUES (?, ?, ?, ?)',
        (scan_id, domain, 'created', rate_limit)
    )
    conn.commit()
    conn.close()
    
    # Load settings
    settings = load_settings()
    rotate_ua = settings.get('rotate_user_agents', False)
    
    # Create scanner instance but don't start it
    scanner = DomScoutScanner(scan_id, domain, rate_limit, RESOLVERS_FILE, SCREENSHOTS_DIR, rotate_ua)
    active_scans[scan_id] = scanner
    
    return jsonify({'scan_id': scan_id, 'status': 'created'})


@app.route('/api/scan', methods=['POST'])
def start_scan():
    """Start a new scan"""
    data = request.json
    domain = data.get('domain')
    rate_limit = data.get('rate_limit', 150)
    
    if not domain:
        return jsonify({'error': 'Domain is required'}), 400
    
    # Generate unique scan ID
    scan_id = str(uuid.uuid4())
    
    # Create scan record
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO scans (id, domain, status, rate_limit) VALUES (?, ?, ?, ?)',
        (scan_id, domain, 'running', rate_limit)
    )
    conn.commit()
    conn.close()
    
    # Load settings
    settings = load_settings()
    rotate_ua = settings.get('rotate_user_agents', False)
    
    # Start scan in background thread
    scanner = DomScoutScanner(scan_id, domain, rate_limit, RESOLVERS_FILE, SCREENSHOTS_DIR, rotate_ua)
    active_scans[scan_id] = scanner
    
    thread = threading.Thread(target=run_scan, args=(scanner,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'scan_id': scan_id, 'status': 'started'})


def run_scan(scanner):
    """Run the scan in background"""
    try:
        scanner.run()
        
        # Update scan status
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE scans SET status = ?, completed_at = ?, duration = ? WHERE id = ?',
            ('completed', datetime.now(), scanner.duration, scanner.scan_id)
        )
        conn.commit()
        
        # Save results to database
        save_scan_results(scanner)
        
        conn.close()
    except Exception as e:
        print(f"Scan failed: {e}")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE scans SET status = ? WHERE id = ?',
            ('failed', scanner.scan_id)
        )
        conn.commit()
        conn.close()


def save_scan_results(scanner):
    """Save scan results to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Save subdomains
    for subdomain in scanner.subdomains:
        cursor.execute(
            'INSERT INTO subdomains (scan_id, subdomain) VALUES (?, ?)',
            (scanner.scan_id, subdomain)
        )
    
    # Save URLs
    for url_data in scanner.urls:
        cursor.execute(
            'INSERT INTO urls (scan_id, url, status_code) VALUES (?, ?, ?)',
            (scanner.scan_id, url_data['url'], url_data.get('status_code'))
        )
    
    # Save screenshots
    for screenshot in scanner.screenshots:
        cursor.execute(
            'INSERT INTO screenshots (scan_id, url, filename, status_code, title, headers, roi_score) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (scanner.scan_id, screenshot['url'], screenshot['filename'], 
             screenshot.get('status_code'), screenshot.get('title'), 
             json.dumps(screenshot.get('headers', {})), screenshot.get('roi_score', 50))
        )
    
    conn.commit()
    conn.close()


@app.route('/api/scan/<scan_id>', methods=['GET'])
def get_scan_info(scan_id):
    """Get scan information and progress"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    scan = cursor.execute('SELECT * FROM scans WHERE id = ?', (scan_id,)).fetchone()
    if not scan:
        conn.close()
        return jsonify({'error': 'Scan not found'}), 404
    
    # Get statistics
    subdomains_count = cursor.execute(
        'SELECT COUNT(*) FROM subdomains WHERE scan_id = ?', (scan_id,)
    ).fetchone()[0]
    
    urls_count = cursor.execute(
        'SELECT COUNT(*) FROM urls WHERE scan_id = ?', (scan_id,)
    ).fetchone()[0]
    
    screenshots_count = cursor.execute(
        'SELECT COUNT(*) FROM screenshots WHERE scan_id = ?', (scan_id,)
    ).fetchone()[0]
    
    conn.close()
    
    # Get progress from active scanner
    progress = 0
    message = 'Initializing...'
    
    if scan_id in active_scans:
        scanner = active_scans[scan_id]
        progress = scanner.progress
        message = scanner.progress_message
    elif scan['status'] == 'completed':
        progress = 100
        message = 'Completed'
    
    return jsonify({
        'scan': dict(scan),
        'stats': {
            'subdomains': subdomains_count,
            'alive_urls': urls_count,
            'screenshots': screenshots_count
        },
        'progress': progress,
        'message': message
    })


@app.route('/api/scan/<scan_id>/subdomains', methods=['GET'])
def get_subdomains(scan_id):
    """Get subdomains for a scan"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    rows = cursor.execute(
        'SELECT subdomain FROM subdomains WHERE scan_id = ? ORDER BY subdomain',
        (scan_id,)
    ).fetchall()
    
    conn.close()
    
    subdomains = [row['subdomain'] for row in rows]
    return jsonify({'subdomains': subdomains})


@app.route('/api/scan/<scan_id>/urls', methods=['GET'])
def get_urls(scan_id):
    """Get URLs for a scan"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    rows = cursor.execute(
        'SELECT url, status_code FROM urls WHERE scan_id = ? ORDER BY url',
        (scan_id,)
    ).fetchall()
    
    conn.close()
    
    urls = [dict(row) for row in rows]
    return jsonify({'urls': urls})


@app.route('/api/scan/<scan_id>/screenshots', methods=['GET'])
def get_screenshots(scan_id):
    """Get screenshots for a scan"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    rows = cursor.execute(
        'SELECT * FROM screenshots WHERE scan_id = ? ORDER BY roi_score DESC, url',
        (scan_id,)
    ).fetchall()
    
    conn.close()
    
    screenshots = []
    for row in rows:
        screenshot = dict(row)
        if screenshot.get('headers'):
            try:
                screenshot['headers'] = json.loads(screenshot['headers'])
            except:
                pass
        screenshots.append(screenshot)
    
    return jsonify({'screenshots': screenshots})


@app.route('/api/scan/<scan_id>/tools', methods=['GET'])
def get_tools_status(scan_id):
    """Get the status of individual tools"""
    scanner = None
    
    # Try to get scanner from active scans
    if scan_id in active_scans:
        scanner = active_scans[scan_id]
    else:
        # Create scanner from database/filesystem to read status
        conn = get_db_connection()
        cursor = conn.cursor()
        scan = cursor.execute('SELECT * FROM scans WHERE id = ?', (scan_id,)).fetchone()
        conn.close()
        
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404
        
        # Load settings
        settings = load_settings()
        rotate_ua = settings.get('rotate_user_agents', False)
        
        scanner = DomScoutScanner(
            scan_id,
            scan['domain'],
            scan['rate_limit'] or 150,
            RESOLVERS_FILE,
            SCREENSHOTS_DIR,
            rotate_ua
        )
        
        # Load counts from filesystem
        scan_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), f'scan_{scan_id}')
        if os.path.exists(scan_dir):
            for tool_name in scanner.tools_status.keys():
                file_map = {
                    'subfinder': 'subfinder-rescursive.txt',
                    'findomain': 'findomain.txt',
                    'assetfinder': 'assetfinder.txt',
                    'sublist3r': 'sublist3r.txt',
                    'merge': 'subdomains.txt',
                    'dnsx': 'live_subs.txt',
                    'httpx': 'alive_webservices.txt',
                    'gau': 'gau_urls.txt',
                    'gospider': 'gospider_urls.txt',
                    'merge2': 'all_urls_merged.txt',
                    'gowitness': 'gowitness.sqlite3'
                }
                
                filename = file_map.get(tool_name)
                if filename:
                    filepath = os.path.join(scan_dir, filename)
                    if os.path.exists(filepath):
                        scanner.tools_status[tool_name]['status'] = 'completed'
                        
                        # Count lines for text files
                        if filename.endswith('.txt'):
                            try:
                                with open(filepath, 'r') as f:
                                    count = sum(1 for line in f if line.strip())
                                    scanner.tools_status[tool_name]['count'] = count
                            except:
                                pass
                        elif tool_name == 'gowitness':
                            # Check screenshots from database
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            count = cursor.execute(
                                'SELECT COUNT(*) FROM screenshots WHERE scan_id = ?',
                                (scan_id,)
                            ).fetchone()[0]
                            scanner.tools_status[tool_name]['count'] = count
                            conn.close()
    
    tools = scanner.get_tools_status()
    return jsonify({'tools': tools})


@app.route('/api/scan/<scan_id>/tool/<tool_name>', methods=['POST'])
def run_individual_tool(scan_id, tool_name):
    """Run an individual tool"""
    if scan_id not in active_scans:
        return jsonify({'error': 'Scan not found'}), 404
    
    scanner = active_scans[scan_id]
    
    # Start tool in background thread
    thread = threading.Thread(target=run_tool_async, args=(scanner, tool_name))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'tool': tool_name, 'status': 'started'})


@app.route('/api/scan/<scan_id>/auto', methods=['POST'])
def run_auto_scan(scan_id):
    """Run all tools automatically in sequence"""
    if scan_id not in active_scans:
        return jsonify({'error': 'Scan not found'}), 404
    
    scanner = active_scans[scan_id]
    
    # Update scan status
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE scans SET status = ? WHERE id = ?', ('running', scan_id))
    conn.commit()
    conn.close()
    
    # Start auto scan in background
    thread = threading.Thread(target=run_scan, args=(scanner,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'status': 'started'})


def run_tool_async(scanner, tool_name):
    """Run a single tool asynchronously"""
    try:
        scanner.run_single_tool(tool_name)
        
        # Save results to database after tool completion
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if tool_name == 'merge':
            # Save subdomains after merge
            # First delete existing subdomains for this scan
            cursor.execute('DELETE FROM subdomains WHERE scan_id = ?', (scanner.scan_id,))
            for subdomain in scanner.subdomains:
                cursor.execute(
                    'INSERT INTO subdomains (scan_id, subdomain) VALUES (?, ?)',
                    (scanner.scan_id, subdomain)
                )
        
        elif tool_name == 'dnsx':
            # Save live subdomains after dnsx
            # DNSx results are stored in scanner.live_subdomains
            cursor.execute('DELETE FROM subdomains WHERE scan_id = ?', (scanner.scan_id,))
            for subdomain in scanner.live_subdomains:
                cursor.execute(
                    'INSERT INTO subdomains (scan_id, subdomain) VALUES (?, ?)',
                    (scanner.scan_id, subdomain)
                )
        
        elif tool_name == 'httpx':
            # Save URLs after httpx
            # First delete existing urls for this scan
            cursor.execute('DELETE FROM urls WHERE scan_id = ?', (scanner.scan_id,))
            for url_data in scanner.urls:
                cursor.execute(
                    'INSERT INTO urls (scan_id, url, status_code) VALUES (?, ?, ?)',
                    (scanner.scan_id, url_data['url'], url_data.get('status_code'))
                )
        
        elif tool_name == 'merge2':
            # Save merged URLs after merge2
            # First delete existing urls for this scan
            cursor.execute('DELETE FROM urls WHERE scan_id = ?', (scanner.scan_id,))
            # Read from all_urls_merged.txt
            merged_file = os.path.join(scanner.scan_dir, "all_urls_merged.txt")
            if os.path.exists(merged_file):
                with open(merged_file, 'r') as f:
                    for line in f:
                        url = line.strip()
                        if url:
                            cursor.execute(
                                'INSERT INTO urls (scan_id, url, status_code) VALUES (?, ?, ?)',
                                (scanner.scan_id, url, None)
                            )
        
        elif tool_name == 'gowitness':
            # Save screenshots after gowitness
            # First delete existing screenshots for this scan
            cursor.execute('DELETE FROM screenshots WHERE scan_id = ?', (scanner.scan_id,))
            for screenshot in scanner.screenshots:
                cursor.execute(
                    'INSERT INTO screenshots (scan_id, url, filename, status_code, title, headers, roi_score) VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (scanner.scan_id, screenshot['url'], screenshot['filename'], 
                     screenshot.get('status_code'), screenshot.get('title'), 
                     json.dumps(screenshot.get('headers', {})), screenshot.get('roi_score', 50))
                )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Tool {tool_name} failed: {e}")


@app.route('/api/scan/<scan_id>/tool/<tool_name>/results', methods=['GET'])
def get_tool_results(scan_id, tool_name):
    """Get results from a specific tool"""
    scanner = None
    
    # Try to get scanner from active scans
    if scan_id in active_scans:
        scanner = active_scans[scan_id]
    else:
        # Create scanner from database/filesystem
        conn = get_db_connection()
        cursor = conn.cursor()
        scan = cursor.execute('SELECT * FROM scans WHERE id = ?', (scan_id,)).fetchone()
        conn.close()
        
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404
        
        # Load settings
        settings = load_settings()
        rotate_ua = settings.get('rotate_user_agents', False)
        
        # Create scanner instance to read results from filesystem
        scanner = DomScoutScanner(
            scan_id,
            scan['domain'],
            scan['rate_limit'] or 150,
            RESOLVERS_FILE,
            SCREENSHOTS_DIR,
            rotate_ua
        )
    
    results = scanner.get_tool_results(tool_name)
    return jsonify({'results': results, 'tool': tool_name})


@app.route('/api/scan/<scan_id>', methods=['DELETE'])
def delete_scan(scan_id):
    """Delete a scan and all its data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete from all tables
        cursor.execute('DELETE FROM screenshots WHERE scan_id = ?', (scan_id,))
        cursor.execute('DELETE FROM urls WHERE scan_id = ?', (scan_id,))
        cursor.execute('DELETE FROM subdomains WHERE scan_id = ?', (scan_id,))
        cursor.execute('DELETE FROM scans WHERE id = ?', (scan_id,))
        
        conn.commit()
        conn.close()
        
        # Remove from active scans
        if scan_id in active_scans:
            del active_scans[scan_id]
        
        # Delete scan directory
        scan_dir = os.path.join(os.path.dirname(SCREENSHOTS_DIR), f'scan_{scan_id}')
        if os.path.exists(scan_dir):
            shutil.rmtree(scan_dir)
        
        # Delete screenshots directory
        scan_screenshots = os.path.join(SCREENSHOTS_DIR, scan_id)
        if os.path.exists(scan_screenshots):
            shutil.rmtree(scan_screenshots)
        
        return jsonify({'success': True, 'message': 'Scan deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scans', methods=['GET'])
def get_scans():
    """Get all scans"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    rows = cursor.execute(
        'SELECT s.*, '
        '(SELECT COUNT(*) FROM subdomains WHERE scan_id = s.id) as subdomains_count, '
        '(SELECT COUNT(*) FROM urls WHERE scan_id = s.id) as urls_count '
        'FROM scans s ORDER BY created_at DESC LIMIT 10'
    ).fetchall()
    
    conn.close()
    
    scans = [dict(row) for row in rows]
    return jsonify({'scans': scans})


@app.route('/screenshots/<path:filename>')
def serve_screenshot(filename):
    """Serve screenshot files"""
    return send_from_directory(SCREENSHOTS_DIR, filename)


# ========== SETTINGS ENDPOINTS ==========

def load_settings():
    """Load settings from JSON file"""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'rotate_user_agents': False}


def save_settings(settings):
    """Save settings to JSON file"""
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings"""
    settings = load_settings()
    return jsonify({'settings': settings})


@app.route('/api/settings/user-agents', methods=['POST'])
def update_user_agents_setting():
    """Update user-agents rotation setting"""
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        
        settings = load_settings()
        settings['rotate_user_agents'] = enabled
        
        if save_settings(settings):
            return jsonify({'success': True, 'message': 'Settings updated'})
        else:
            return jsonify({'success': False, 'error': 'Failed to save settings'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/subfinder-config', methods=['GET'])
def get_subfinder_config():
    """Get subfinder provider config"""
    try:
        if os.path.exists(SUBFINDER_CONFIG_PATH):
            with open(SUBFINDER_CONFIG_PATH, 'r') as f:
                content = f.read()
            return jsonify({'success': True, 'content': content, 'path': SUBFINDER_CONFIG_PATH})
        else:
            return jsonify({'success': True, 'content': '', 'path': SUBFINDER_CONFIG_PATH, 'message': 'File does not exist yet'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/settings/subfinder-config', methods=['POST'])
def update_subfinder_config():
    """Update subfinder provider config"""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        # Ensure directory exists
        config_dir = os.path.dirname(SUBFINDER_CONFIG_PATH)
        os.makedirs(config_dir, exist_ok=True)
        
        # Write config file
        with open(SUBFINDER_CONFIG_PATH, 'w') as f:
            f.write(content)
        
        return jsonify({'success': True, 'message': 'Subfinder config updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    init_db()
    print("=" * 60)
    print("DomScout v2 Server Starting...")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print(f"Screenshots: {SCREENSHOTS_DIR}")
    print(f"Resolvers: {RESOLVERS_FILE}")
    print("=" * 60)
    print("Server running at http://localhost:5000")
    print("Frontend will be available after building Vue.js")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
