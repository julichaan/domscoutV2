#!/usr/bin/env python3
import os
import json
import time
import threading
import sqlite3
import tempfile
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
TEMP_SCANS_DIR = os.path.join(tempfile.gettempdir(), 'domscout_scans')
RESOLVERS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resolvers.txt')
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'settings.json')
SUBFINDER_CONFIG_PATH = os.path.expanduser('~/.config/subfinder/provider-config.yaml')

TOOL_NAMES = [
    'subfinder', 'findomain', 'assetfinder', 'sublist3r',
    'merge', 'dnsx', 'httpx', 'gau', 'gospider', 'merge2', 'gowitness'
]

# Ensure directories exist
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(TEMP_SCANS_DIR, exist_ok=True)

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
deleted_scans = set()


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
            title TEXT,
            webserver TEXT,
            technologies TEXT,
            content_length INTEGER,
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

    # Tool status cache table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tool_status (
            scan_id TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            status TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (scan_id, tool_name),
            FOREIGN KEY (scan_id) REFERENCES scans(id)
        )
    ''')

    # Tool results cache table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tool_results (
            scan_id TEXT NOT NULL,
            tool_name TEXT NOT NULL,
            results_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (scan_id, tool_name),
            FOREIGN KEY (scan_id) REFERENCES scans(id)
        )
    ''')

    # Lightweight schema migration for existing databases
    url_columns = {
        row[1] for row in cursor.execute('PRAGMA table_info(urls)').fetchall()
    }
    if 'title' not in url_columns:
        cursor.execute('ALTER TABLE urls ADD COLUMN title TEXT')
    if 'webserver' not in url_columns:
        cursor.execute('ALTER TABLE urls ADD COLUMN webserver TEXT')
    if 'technologies' not in url_columns:
        cursor.execute('ALTER TABLE urls ADD COLUMN technologies TEXT')
    if 'content_length' not in url_columns:
        cursor.execute('ALTER TABLE urls ADD COLUMN content_length INTEGER')
    
    conn.commit()
    conn.close()


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn


def scan_exists(conn, scan_id):
    """Check whether scan record still exists."""
    cursor = conn.cursor()
    row = cursor.execute('SELECT 1 FROM scans WHERE id = ?', (scan_id,)).fetchone()
    return row is not None


def upsert_tool_status(conn, scan_id, tool_name, status, count):
    """Insert or update tool status in SQLite cache."""
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO tool_status (scan_id, tool_name, status, count, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(scan_id, tool_name) DO UPDATE SET
            status=excluded.status,
            count=excluded.count,
            updated_at=CURRENT_TIMESTAMP
        ''',
        (scan_id, tool_name, status, count)
    )


def upsert_tool_results(conn, scan_id, tool_name, results):
    """Insert or update tool results in SQLite cache."""
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO tool_results (scan_id, tool_name, results_json, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(scan_id, tool_name) DO UPDATE SET
            results_json=excluded.results_json,
            updated_at=CURRENT_TIMESTAMP
        ''',
        (scan_id, tool_name, json.dumps(results))
    )


def load_tool_status_from_db(scan_id):
    """Load tool status map for a scan from SQLite cache."""
    status_map = {tool: {'status': 'idle', 'count': 0} for tool in TOOL_NAMES}

    conn = get_db_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        'SELECT tool_name, status, count FROM tool_status WHERE scan_id = ?',
        (scan_id,)
    ).fetchall()
    conn.close()

    for row in rows:
        tool_name = row['tool_name']
        if tool_name in status_map:
            status_map[tool_name] = {
                'status': row['status'],
                'count': row['count'] or 0
            }

    return status_map


def load_tool_results_from_db(scan_id, tool_name):
    """Load tool results array for a scan/tool from SQLite cache."""
    conn = get_db_connection()
    cursor = conn.cursor()
    row = cursor.execute(
        'SELECT results_json FROM tool_results WHERE scan_id = ? AND tool_name = ?',
        (scan_id, tool_name)
    ).fetchone()
    conn.close()

    if not row:
        return []

    try:
        return json.loads(row['results_json'])
    except Exception:
        return []


def save_tool_cache(scanner):
    """Persist current tool statuses and results for the scan."""
    conn = get_db_connection()
    try:
        for tool_name, data in scanner.get_tools_status().items():
            upsert_tool_status(
                conn,
                scanner.scan_id,
                tool_name,
                data.get('status', 'idle'),
                data.get('count', 0)
            )
            upsert_tool_results(
                conn,
                scanner.scan_id,
                tool_name,
                scanner.get_tool_results(tool_name)
            )
        conn.commit()
    finally:
        conn.close()


def serialize_technologies(technologies):
    """Serialize technologies metadata into JSON text."""
    if technologies is None:
        return None

    if isinstance(technologies, str):
        value = technologies.strip()
        if not value:
            return None
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return json.dumps(parsed)
        except Exception:
            pass
        return json.dumps([item.strip() for item in value.split(',') if item.strip()])

    if isinstance(technologies, list):
        return json.dumps([str(item).strip() for item in technologies if str(item).strip()])

    return None


def parse_technologies(technologies_json):
    """Parse technologies JSON text into a normalized list."""
    if not technologies_json:
        return []
    try:
        parsed = json.loads(technologies_json)
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    except Exception:
        pass
    return []


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
    scanner = DomScoutScanner(
        scan_id,
        domain,
        rate_limit,
        RESOLVERS_FILE,
        SCREENSHOTS_DIR,
        rotate_ua,
        TEMP_SCANS_DIR
    )
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
    scanner = DomScoutScanner(
        scan_id,
        domain,
        rate_limit,
        RESOLVERS_FILE,
        SCREENSHOTS_DIR,
        rotate_ua,
        TEMP_SCANS_DIR
    )
    active_scans[scan_id] = scanner
    
    thread = threading.Thread(target=run_scan, args=(scanner,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'scan_id': scan_id, 'status': 'started'})


def run_scan(scanner):
    """Run the scan in background"""
    try:
        scanner.run()

        if scanner.scan_id in deleted_scans:
            return

        conn = get_db_connection()
        if not scan_exists(conn, scanner.scan_id):
            conn.close()
            return
        
        # Update scan status
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE scans SET status = ?, completed_at = ?, duration = ? WHERE id = ?',
            ('completed', datetime.now(), scanner.duration, scanner.scan_id)
        )
        conn.commit()
        
        # Save results to database
        save_scan_results(scanner)

        # Persist per-tool statuses and results in SQLite
        save_tool_cache(scanner)
        
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
        try:
            save_tool_cache(scanner)
        except Exception:
            pass
    finally:
        try:
            scanner.cleanup_temp_artifacts()
        except Exception:
            pass

        if scanner.scan_id in active_scans:
            del active_scans[scanner.scan_id]

        if scanner.scan_id in deleted_scans:
            deleted_scans.remove(scanner.scan_id)


def save_scan_results(scanner):
    """Save scan results to database"""
    conn = get_db_connection()
    cursor = conn.cursor()

    if scanner.scan_id in deleted_scans or not scan_exists(conn, scanner.scan_id):
        conn.close()
        return

    # Replace previous persisted data for idempotency
    cursor.execute('DELETE FROM subdomains WHERE scan_id = ?', (scanner.scan_id,))
    cursor.execute('DELETE FROM urls WHERE scan_id = ?', (scanner.scan_id,))
    cursor.execute('DELETE FROM screenshots WHERE scan_id = ?', (scanner.scan_id,))
    
    # Save subdomains
    for subdomain in scanner.subdomains:
        cursor.execute(
            'INSERT INTO subdomains (scan_id, subdomain) VALUES (?, ?)',
            (scanner.scan_id, subdomain)
        )
    
    # Save URLs
    by_url = {}
    for url_data in scanner.urls:
        url = url_data.get('url')
        if not url:
            continue
        if url not in by_url:
            by_url[url] = {
                'url': url,
                'status_code': None,
                'title': None,
                'webserver': None,
                'technologies': None,
                'content_length': None
            }

        existing = by_url[url]
        for key in ['status_code', 'title', 'webserver', 'technologies', 'content_length']:
            value = url_data.get(key)
            if value not in (None, '', []):
                existing[key] = value

    for url_data in by_url.values():
        cursor.execute(
            '''
            INSERT INTO urls (scan_id, url, status_code, title, webserver, technologies, content_length)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                scanner.scan_id,
                url_data['url'],
                url_data.get('status_code'),
                url_data.get('title'),
                url_data.get('webserver'),
                serialize_technologies(url_data.get('technologies')),
                url_data.get('content_length')
            )
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
        '''
        SELECT url, status_code, title, webserver, technologies, content_length
        FROM urls
        WHERE scan_id = ?
        ORDER BY url
        ''',
        (scan_id,)
    ).fetchall()
    
    conn.close()
    
    urls = []
    for row in rows:
        item = dict(row)
        item['technologies'] = parse_technologies(item.get('technologies'))
        urls.append(item)

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
    # Try to get scanner from active scans
    if scan_id in active_scans:
        tools = active_scans[scan_id].get_tools_status()
    else:
        # Load from SQLite cache for finished/non-active scans
        conn = get_db_connection()
        cursor = conn.cursor()
        scan = cursor.execute('SELECT id FROM scans WHERE id = ?', (scan_id,)).fetchone()
        conn.close()

        if not scan:
            return jsonify({'error': 'Scan not found'}), 404

        tools = load_tool_status_from_db(scan_id)

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

        if scanner.scan_id in deleted_scans:
            return
        
        # Save results to database after tool completion
        conn = get_db_connection()
        cursor = conn.cursor()

        if not scan_exists(conn, scanner.scan_id):
            conn.close()
            return
        
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
                    '''
                    INSERT INTO urls (scan_id, url, status_code, title, webserver, technologies, content_length)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        scanner.scan_id,
                        url_data['url'],
                        url_data.get('status_code'),
                        url_data.get('title'),
                        url_data.get('webserver'),
                        serialize_technologies(url_data.get('technologies')),
                        url_data.get('content_length')
                    )
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
                                '''
                                INSERT INTO urls (scan_id, url, status_code, title, webserver, technologies, content_length)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                                ''',
                                (scanner.scan_id, url, None, None, None, None, None)
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

        # Persist current status/results cache for this tool
        tool_data = scanner.get_tools_status().get(tool_name, {'status': 'idle', 'count': 0})
        upsert_tool_status(
            conn,
            scanner.scan_id,
            tool_name,
            tool_data.get('status', 'idle'),
            tool_data.get('count', 0)
        )
        upsert_tool_results(
            conn,
            scanner.scan_id,
            tool_name,
            scanner.get_tool_results(tool_name)
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Tool {tool_name} failed: {e}")
        try:
            conn = get_db_connection()
            tool_data = scanner.get_tools_status().get(tool_name, {'status': 'failed', 'count': 0})
            upsert_tool_status(
                conn,
                scanner.scan_id,
                tool_name,
                tool_data.get('status', 'failed'),
                tool_data.get('count', 0)
            )
            upsert_tool_results(conn, scanner.scan_id, tool_name, [])
            conn.commit()
            conn.close()
        except Exception:
            pass


@app.route('/api/scan/<scan_id>/tool/<tool_name>/results', methods=['GET'])
def get_tool_results(scan_id, tool_name):
    """Get results from a specific tool"""
    # Try to get scanner from active scans
    if scan_id in active_scans:
        results = active_scans[scan_id].get_tool_results(tool_name)
    else:
        # Read from SQLite cache for finished/non-active scans
        conn = get_db_connection()
        cursor = conn.cursor()
        scan = cursor.execute('SELECT * FROM scans WHERE id = ?', (scan_id,)).fetchone()
        conn.close()
        
        if not scan:
            return jsonify({'error': 'Scan not found'}), 404

        results = load_tool_results_from_db(scan_id, tool_name)

    return jsonify({'results': results, 'tool': tool_name})


@app.route('/api/scan/<scan_id>', methods=['DELETE'])
def delete_scan(scan_id):
    """Delete a scan and all its data"""
    try:
        deleted_scans.add(scan_id)

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete from all tables
        cursor.execute('DELETE FROM screenshots WHERE scan_id = ?', (scan_id,))
        cursor.execute('DELETE FROM urls WHERE scan_id = ?', (scan_id,))
        cursor.execute('DELETE FROM subdomains WHERE scan_id = ?', (scan_id,))
        cursor.execute('DELETE FROM tool_results WHERE scan_id = ?', (scan_id,))
        cursor.execute('DELETE FROM tool_status WHERE scan_id = ?', (scan_id,))
        cursor.execute('DELETE FROM scans WHERE id = ?', (scan_id,))
        
        conn.commit()
        conn.close()
        
        # Remove from active scans
        if scan_id in active_scans:
            del active_scans[scan_id]
        
        # Delete scan directory
        scan_dir = os.path.join(TEMP_SCANS_DIR, f'scan_{scan_id}')
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
    print(f"Temporary scans: {TEMP_SCANS_DIR}")
    print(f"Resolvers: {RESOLVERS_FILE}")
    print("=" * 60)
    print("Server running at http://localhost:5000")
    print("Frontend will be available after building Vue.js")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
