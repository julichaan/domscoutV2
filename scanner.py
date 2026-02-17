#!/usr/bin/env python3
import subprocess
import os
import time
import concurrent.futures
import shutil
import platform
import json
import sqlite3
import logging
import sys
import random


# Configure logging to output to both console and a log file
log_dir = os.path.expanduser("~/domscout_logs")
os.makedirs(log_dir, exist_ok=True)

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

def setup_logging(scan_id):
    """Setup logging for a specific scan"""
    log_file = os.path.join(log_dir, f"scan_{scan_id}.log")
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    
    # Console handler (for import into app.py logging)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    
    # Create scanner logger
    logger = logging.getLogger(f'scanner_{scan_id}')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger


class DomScoutScanner:
    def __init__(self, scan_id, target, rate_limit, resolvers_file, screenshots_dir, rotate_user_agents=False):
        self.scan_id = scan_id
        self.target = target
        self.rate_limit = rate_limit
        self.resolvers_file = resolvers_file
        self.screenshots_dir = screenshots_dir
        self.rotate_user_agents = rotate_user_agents
        
        # Setup logging for this scan
        self.logger = setup_logging(scan_id)
        self.logger.info(f"=== SCAN STARTED for {target} ===")
        
        # Create scan-specific directory
        self.scan_dir = os.path.join(os.path.dirname(screenshots_dir), f'scan_{scan_id}')
        os.makedirs(self.scan_dir, exist_ok=True)
        self.logger.debug(f"Scan directory: {self.scan_dir}")
        
        # Results
        self.subdomains = []
        self.live_subdomains = []
        self.urls = []
        self.screenshots = []
        
        # Progress tracking
        self.total_steps = 9
        self.current_step = 0
        self.progress = 0
        self.progress_message = "Initializing..."
        
        # Timing
        self.start_time = None
        self.duration = 0
        
        # Tool status tracking
        self.tools_status = {
            'subfinder': {'status': 'idle', 'count': 0},
            'findomain': {'status': 'idle', 'count': 0},
            'assetfinder': {'status': 'idle', 'count': 0},
            'sublist3r': {'status': 'idle', 'count': 0},
            'merge': {'status': 'idle', 'count': 0},
            'dnsx': {'status': 'idle', 'count': 0},
            'httpx': {'status': 'idle', 'count': 0},
            'gau': {'status': 'idle', 'count': 0},
            'gospider': {'status': 'idle', 'count': 0},
            'merge2': {'status': 'idle', 'count': 0},
            'gowitness': {'status': 'idle', 'count': 0}
        }
        
        # Temp files
        self.temp_files = [
            os.path.join(self.scan_dir, "subfinder-rescursive.txt"),
            os.path.join(self.scan_dir, "findomain.txt"),
            os.path.join(self.scan_dir, "assetfinder.txt"),
            os.path.join(self.scan_dir, "sublist3r.txt"),
            os.path.join(self.scan_dir, "subdomains.txt"),
            os.path.join(self.scan_dir, "live_subs.txt"),
            os.path.join(self.scan_dir, "alive_webservices.txt"),
            os.path.join(self.scan_dir, "gau_urls.txt"),
            os.path.join(self.scan_dir, "gospider_urls.txt"),
            os.path.join(self.scan_dir, "all_urls_merged.txt")
        ]
    
    def update_progress(self, step, message):
        """Update scan progress"""
        self.current_step = step
        self.progress_message = message
        self.progress = (step / self.total_steps) * 100
    
    def get_random_user_agent(self):
        """Get a random user agent from the list"""
        return random.choice(USER_AGENTS)
    
    def run_command(self, command):
        """Run a shell command and log output"""
        try:
            self.logger.debug(f"Running command: {command[:200]}...")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.scan_dir
            )
            if result.returncode != 0:
                self.logger.warning(f"Command failed with code {result.returncode}")
                if result.stderr:
                    self.logger.warning(f"stderr: {result.stderr[:500]}")
            else:
                self.logger.debug(f"Command completed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Command exception: {e}")
            pass
    
    def get_chrome_path(self):
        """Get Chrome binary path"""
        system = platform.system()
        if system == "Linux":
            paths = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
            for path in paths:
                if shutil.which(path):
                    return shutil.which(path)
        elif system == "Darwin":
            paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
        return None
    
    def get_tools_status(self):
        """Get the current status of all tools"""
        return self.tools_status
    
    def calculate_roi_score(self, httpx_data, url=''):
        """Calculate ROI score with URL complexity analysis
        
        Args:
            httpx_data: Dictionary with httpx response data
            url: Optional URL for additional pattern/complexity analysis
        """
        score = 50  # Base score
        
        try:
            # URL complexity analysis - add points based on URL patterns and structure
            if url:
                url_lower = url.lower()
                
                # Path depth analysis - deeper paths are more complex
                path_parts = [p for p in url.split('/') if p and p not in ['https:', '', 'http:']]
                if len(path_parts) > 2:  # Deep paths more complex
                    score += min(10, (len(path_parts) - 2) * 2)
                
                # URL length (longer = potentially more complex)
                if len(url) > 100:
                    score += 5
                
                # Special patterns indicating functionality/complexity
                special_patterns = {
                    'api': 5,
                    'admin': 5,
                    'config': 4,
                    'settings': 3,
                    'account': 2,
                    'user': 2,
                    'login': 3,
                    'auth': 3,
                    'download': 2,
                    'upload': 2,
                    'search': 2,
                }
                for pattern, points in special_patterns.items():
                    if f'/{pattern}' in url_lower or f'?{pattern}' in url_lower or f'&{pattern}' in url_lower:
                        score += points
                        break  # Only count first matching pattern
            
            # Extract data from httpx response
            status_code = httpx_data.get('status-code', 200)
            content_length = httpx_data.get('content-length', 0)
            webserver = httpx_data.get('webserver', '').lower()
            headers = httpx_data.get('headers', {})
            
            # Status code weights
            if status_code == 404:
                score += 50
            elif status_code == 403:
                score += 20
            elif status_code == 401:
                score += 15
            elif status_code >= 500:
                score += 15
            elif status_code >= 400:
                score += 10
            
            # Header Analysis
            if isinstance(headers, dict):
                header_keys_lower = [h.lower() for h in headers.keys()]
                
                #  Caching
                if any(h in header_keys_lower for h in ['cache-control', 'etag', 'expires', 'vary']):
                    score += 10
                
                # Missing security headers
                missing = sum(1 for h in ['x-frame-options', 'x-content-type-options', 'strict-transport-security']
                              if h not in header_keys_lower)
                if missing >= 2:
                    score += missing * 3
                
                # Tech indicators
                if any(h in header_keys_lower for h in ['x-powered-by', 'server', 'x-aspnet-version']):
                    score += 3
            
            # CSP
            csp = httpx_data.get('csp', {})
            if csp and isinstance(csp, dict) and len(csp.get('domains', [])) > 10:
                score += 5
            elif status_code == 200 and content_length > 1000 and not csp:
                score += 10
            
            # Content complexity
            if content_length > 100000:
                score += 3
            elif content_length > 50000:
                score += 2
            elif content_length > 10000:
                score += 1
            
            if webserver:
                score += 2
            
            return max(50, min(250, round(score)))
        except Exception as e:
            self.logger.error(f"Error calculating ROI score: {e}")
            return 50
    
    def get_tool_results(self, tool_name):
        """Get results from a specific tool"""
        results = []
        
        # Special handling for gowitness - return scored and sorted results
        if tool_name == 'gowitness':
            scored_file = os.path.join(self.scan_dir, 'gowitness_scored_results.json')
            if os.path.exists(scored_file):
                try:
                    with open(scored_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Sort by ROI score descending, then by URL
                        sorted_urls = sorted(data, key=lambda x: (-x.get('roi_score', 0), x.get('url', '')))
                        for item in sorted_urls:
                            results.append(f"{item['url']} [ROI: {item.get('roi_score', 0)}]")
                except Exception as e:
                    self.logger.error(f"Error reading scored results: {e}")
            return results
        
        # Map tool names to their result files
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
            'merge2': 'all_urls_merged.txt'
        }
        
        filename = file_map.get(tool_name)
        if not filename:
            return results
        
        filepath = os.path.join(self.scan_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        clean_line = line.strip()
                        if clean_line:
                            results.append(clean_line)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
        
        return results
    
    def run_single_tool(self, tool_name):
        """Run a single tool"""
        self.logger.debug(f"Starting tool: {tool_name}")
        self.tools_status[tool_name]['status'] = 'running'
        
        try:
            if tool_name == 'subfinder':
                self._run_subfinder()
            elif tool_name == 'findomain':
                self._run_findomain()
            elif tool_name == 'assetfinder':
                self._run_assetfinder()
            elif tool_name == 'sublist3r':
                self._run_sublist3r()
            elif tool_name == 'merge':
                self._run_merge()
            elif tool_name == 'dnsx':
                self._run_dnsx_tool()
            elif tool_name == 'httpx':
                self._run_httpx_tool()
            elif tool_name == 'gau':
                self._run_gau()
            elif tool_name == 'gospider':
                self._run_gospider()
            elif tool_name == 'merge2':
                self._run_merge2()
            elif tool_name == 'gowitness':
                self._run_gowitness_tool()
            
            self.logger.info(f"Tool completed successfully: {tool_name} (count: {self.tools_status[tool_name]['count']})") 
            self.tools_status[tool_name]['status'] = 'completed'
        except Exception as e:
            self.logger.error(f"Tool failed: {tool_name} - {e}")
            self.tools_status[tool_name]['status'] = 'failed'
            raise e
    
    def _run_subfinder(self):
        """Run subfinder"""
        cmd = f"subfinder -d {self.target} -all -silent -o subfinder-rescursive.txt"
        self.run_command(cmd)
        
        # Count results
        filepath = os.path.join(self.scan_dir, "subfinder-rescursive.txt")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.tools_status['subfinder']['count'] = sum(1 for line in f if line.strip())
    
    def _run_findomain(self):
        """Run findomain"""
        cmd = f"findomain --quiet -t {self.target} > findomain.txt"
        self.run_command(cmd)
        
        filepath = os.path.join(self.scan_dir, "findomain.txt")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.tools_status['findomain']['count'] = sum(1 for line in f if line.strip())
    
    def _run_assetfinder(self):
        """Run assetfinder"""
        cmd = f"assetfinder -subs-only {self.target} > assetfinder.txt"
        self.run_command(cmd)
        
        filepath = os.path.join(self.scan_dir, "assetfinder.txt")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.tools_status['assetfinder']['count'] = sum(1 for line in f if line.strip())
    
    def _run_sublist3r(self):
        """Run sublist3r"""
        cmd = f"sublist3r -d {self.target} -t 50 -o sublist3r.txt"
        self.run_command(cmd)
        
        filepath = os.path.join(self.scan_dir, "sublist3r.txt")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.tools_status['sublist3r']['count'] = sum(1 for line in f if line.strip())
    
    def _run_merge(self):
        """Merge and deduplicate all subdomains"""
        count = self.merge_subdomains()
        self.tools_status['merge']['count'] = count
    
    def _run_dnsx_tool(self):
        """Run dnsx"""
        # First merge all subdomains
        self.merge_subdomains()
        self.run_dnsx()
        
        filepath = os.path.join(self.scan_dir, "live_subs.txt")
        if os.path.exists(filepath):
            self.live_subdomains = []
            with open(filepath, 'r') as f:
                for line in f:
                    clean_line = line.strip()
                    if clean_line:
                        self.live_subdomains.append(clean_line)
            self.tools_status['dnsx']['count'] = len(self.live_subdomains)
    
    def _run_httpx_tool(self):
        """Run httpx"""
        self.run_httpx()
        
        # Parse URLs from httpx JSON output AND create alive_webservices.txt
        httpx_json = os.path.join(self.scan_dir, "httpx_output.json")
        alive_file = os.path.join(self.scan_dir, "alive_webservices.txt")
        
        self.logger.info("HTTPx: Parsing output and creating alive_webservices.txt")
        
        if os.path.exists(httpx_json):
            self.urls = []  # Clear previous URLs
            alive_urls = []
            try:
                with open(httpx_json, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            if 'url' in data:
                                url = data['url']
                                self.urls.append({
                                    'url': url,
                                    'status_code': data.get('status_code'),
                                    'title': data.get('title'),
                                    'content_length': data.get('content_length')
                                })
                                alive_urls.append(url)
                        except json.JSONDecodeError:
                            pass
                
                # Write alive URLs to file for GAU/gospider
                with open(alive_file, 'w') as f:
                    for url in alive_urls:
                        f.write(f"{url}\n")
                
                self.logger.info(f"HTTPx: Created {alive_file} with {len(alive_urls)} URLs")
                        
            except Exception as e:
                self.logger.error(f"Error parsing httpx output: {e}")
            self.tools_status['httpx']['count'] = len(self.urls)
        else:
            self.logger.error(f"httpx_output.json not found at {httpx_json}")
    
    def _run_gowitness_tool(self):
        """Run gowitness and calculate ROI scores using httpx data"""
        self.run_gowitness()
        
        self.logger.info("GoWitness: Processing URLs and calculating ROI scores")
        
        # Load httpx data indexed by URL
        httpx_data_list = []
        httpx_json = os.path.join(self.scan_dir, "httpx_output.json")
        
        if os.path.exists(httpx_json):
            try:
                with open(httpx_json, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            if 'url' in data:
                                httpx_data_list.append(data)
                        except json.JSONDecodeError:
                            pass
                self.logger.info(f"GoWitness: Loaded {len(httpx_data_list)} URLs from httpx for ROI scoring")
            except Exception as e:
                self.logger.error(f"Error loading httpx data: {e}")
                httpx_data_list = []
        
        # Try to load from gowitness database first
        gowitness_db = os.path.join(self.scan_dir, "gowitness.sqlite3")
        scored_results = []
        self.screenshots = []
        
        # Check if gowitness database has data
        has_gowitness_data = False
        if os.path.exists(gowitness_db) and os.path.getsize(gowitness_db) > 0:
            try:
                conn = sqlite3.connect(gowitness_db)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                rows = cursor.execute(
                    'SELECT url, final_url, response_code, response_reason, title, filename FROM results WHERE filename IS NOT NULL'
                ).fetchall()
                
                if rows and len(rows) > 0:
                    has_gowitness_data = True
                    self.logger.info(f"GoWitness: Found {len(rows)} entries in database")
                    
                    for row in rows:
                        screenshot_url = row['final_url'] or row['url']
                        filename = row['filename']
                        status_code = row['response_code'] or 200
                        title = row['title'] or ''
                        
                        if not filename:
                            continue
                        
                        # Find matching httpx data
                        httpx_data = None
                        for h_data in httpx_data_list:
                            if self._urls_match(screenshot_url, h_data.get('url', '')):
                                httpx_data = h_data
                                break
                        
                        # Calculate ROI score - use individual status code but httpx data for other factors
                        if httpx_data:
                            # Merge GoWitness status code with httpx data
                            merged_data = dict(httpx_data)
                            merged_data['status-code'] = status_code  # Use individual URL's status code
                            roi_score = self.calculate_roi_score(merged_data, screenshot_url)
                            self.logger.debug(f"ROI with httpx data (status {status_code}): {roi_score} for {screenshot_url}")
                        else:
                            roi_score = self.calculate_roi_score({
                                'status-code': status_code,
                                'content-length': 0,
                                'headers': {}
                            })
                            self.logger.warning(f"No httpx match for {screenshot_url}, base score: {roi_score}")
                        
                        self.screenshots.append({
                            'url': screenshot_url,
                            'status_code': status_code,
                            'title': title,
                            'filename': os.path.join(self.scan_id, os.path.basename(filename)),
                            'roi_score': roi_score
                        })
                        
                        scored_results.append({
                            'url': screenshot_url,
                            'status_code': status_code,
                            'title': title,
                            'roi_score': roi_score,
                            'screenshot': os.path.join(self.scan_id, os.path.basename(filename))
                        })
                
                conn.close()
            except Exception as e:
                self.logger.error(f"Error reading gowitness database: {e}")
                has_gowitness_data = False
        
        # If gowitness database is empty, use httpx data directly
        if not has_gowitness_data and httpx_data_list:
            self.logger.info("GoWitness: Database empty or unavailable, using httpx data directly for ROI scoring")
            
            for httpx_data in httpx_data_list:
                url = httpx_data.get('url', '')
                status_code = httpx_data.get('status-code', 200)
                title = httpx_data.get('title', '')
                
                if not url:
                    continue
                
                roi_score = self.calculate_roi_score(httpx_data)
                
                self.screenshots.append({
                    'url': url,
                    'status_code': status_code,
                    'title': title,
                    'roi_score': roi_score
                })
                
                scored_results.append({
                    'url': url,
                    'status_code': status_code,
                    'title': title,
                    'roi_score': roi_score
                })
        
        if scored_results:
            # Sort by ROI score descending
            scored_results.sort(key=lambda x: -x['roi_score'])
            
            # Save scored results
            scored_results_file = os.path.join(self.scan_dir, 'gowitness_scored_results.json')
            with open(scored_results_file, 'w', encoding='utf-8') as f:
                json.dump(scored_results, f, indent=2)
            
            self.logger.info(f"GoWitness: Processed {len(self.screenshots)} URLs with ROI scores")
            self.logger.info(f"GoWitness: Top scored URLs:")
            for i, result in enumerate(scored_results[:5], 1):
                self.logger.info(f"  {i}. {result['url']} - ROI: {result['roi_score']}")
            
            self.tools_status['gowitness']['count'] = len(self.screenshots)
        else:
            self.logger.warning("GoWitness: No data available for ROI scoring")
            self.tools_status['gowitness']['count'] = 0
    
    def _urls_match(self, url1, url2):
        """Check if two URLs represent the same domain/server"""
        # Normalize URLs
        url1 = url1.rstrip('/').lower()
        url2 = url2.rstrip('/').lower()
        
        # Exact match
        if url1 == url2:
            return True
        
        # Remove default ports
        url1_no_port = url1.replace(':443', '').replace(':80', '')
        url2_no_port = url2.replace(':443', '').replace(':80', '')
        
        if url1_no_port == url2_no_port:
            return True
        
        # Extract domain/host from both URLs
        try:
            from urllib.parse import urlparse
            
            parsed1 = urlparse(url1)
            parsed2 = urlparse(url2)
            
            # Get hostname (without port)
            host1 = parsed1.hostname or parsed1.netloc.split(':')[0]
            host2 = parsed2.hostname or parsed2.netloc.split(':')[0]
            
            # If hostnames match, these are same server
            if host1 and host2 and host1.lower() == host2.lower():
                return True
        except:
            pass
        
        return False
    
    def run(self):
        """Run the full scanning process"""
        try:
            self.start_time = time.time()
            
            # Step 1: Parallel enumeration
            self.update_progress(1, "Running subdomain enumeration tools...")
            self.run_enumeration()
            
            # Step 2: Process and merge results
            self.update_progress(2, "Merging and deduplicating subdomains...")
            self.run_single_tool('merge')
            
            # Step 3: DNS resolution
            self.update_progress(3, "Resolving live subdomains with dnsx...")
            self.run_single_tool('dnsx')
            
            # Step 4: Check alive web services
            self.update_progress(4, "Checking alive web services with httpx...")
            self.run_single_tool('httpx')
            
            # Step 5: Run GAU and gospider in parallel
            self.update_progress(5, "Extracting URLs with GAU and gospider...")
            self.run_url_extraction()
            
            # Step 6: Merge all URLs
            self.update_progress(6, "Merging all URLs...")
            self.run_single_tool('merge2')
            
            # Step 7: Take screenshots
            self.update_progress(7, "Taking screenshots with gowitness...")
            self.run_single_tool('gowitness')
            
            # Step 8: Parse results
            self.update_progress(8, "Processing results...")
            self.parse_results()
            
            # Cleanup
            self.cleanup()
            
            # Auto-delete all temporary .txt files after full scan completion
            self.cleanup_txt_files()
            
            self.duration = int(time.time() - self.start_time)
            self.update_progress(self.total_steps, "Completed!")
            
        except Exception as e:
            print(f"Scan error: {e}")
            raise
    
    def run_enumeration(self):
        """Run parallel subdomain enumeration"""
        tools = ['subfinder', 'findomain', 'assetfinder', 'sublist3r']
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.run_single_tool, tool) for tool in tools]
            concurrent.futures.wait(futures)
    
    def run_url_extraction(self):
        """Run GAU and gospider in parallel"""
        self.logger.info("URL Extraction: Starting parallel execution of GAU and GoSpider")
        
        # Small delay to ensure alive_webservices.txt is fully written
        time.sleep(0.5)
        
        tools = ['gau', 'gospider']
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.run_single_tool, tool) for tool in tools]
            concurrent.futures.wait(futures)
    
    def merge_subdomains(self):
        """Merge and deduplicate subdomains"""
        unique_subdomains = set()
        
        for filename in ["subfinder-rescursive.txt", "findomain.txt", "assetfinder.txt", "sublist3r.txt"]:
            filepath = os.path.join(self.scan_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            clean_line = line.strip()
                            if clean_line:
                                unique_subdomains.add(clean_line)
                except Exception:
                    pass
        
        # Save merged subdomains
        subdomains_file = os.path.join(self.scan_dir, "subdomains.txt")
        with open(subdomains_file, 'w') as f:
            for subdomain in sorted(unique_subdomains):
                f.write(f"{subdomain}\n")
        
        self.subdomains = list(sorted(unique_subdomains))
        return len(unique_subdomains)
    
    def run_dnsx(self):
        """Run dnsx for DNS resolution"""
        subdomains_file = os.path.join(self.scan_dir, "subdomains.txt")
        live_subs_file = os.path.join(self.scan_dir, "live_subs.txt")
        
        if not os.path.exists(subdomains_file) or os.path.getsize(subdomains_file) == 0:
            return
        
        resolvers_abs = os.path.abspath(self.resolvers_file)
        dnsx_cmd = f"dnsx -l {subdomains_file} -r {resolvers_abs} -o {live_subs_file}"
        
        try:
            subprocess.run(
                dnsx_cmd,
                shell=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                cwd=self.scan_dir
            )
        except subprocess.CalledProcessError:
            pass
    
    def run_httpx(self):
        """Run httpx to find alive web services with stealth flags"""
        live_subs_file = os.path.join(self.scan_dir, "live_subs.txt")
        alive_file = os.path.join(self.scan_dir, "alive_webservices.txt")
        httpx_json = os.path.join(self.scan_dir, "httpx_output.json")
        
        if not os.path.exists(live_subs_file) or os.path.getsize(live_subs_file) == 0:
            print("HTTPx: live_subs.txt not found or empty")
            return
        
        # Build user agent option
        if self.rotate_user_agents:
            user_agent = self.get_random_user_agent()
            ua_option = f"-H 'User-Agent: {user_agent}'"
            self.logger.info(f"HTTPx: Using custom user agent rotation")
        else:
            ua_option = "-random-agent"
        
        # Run httpx with stealth flags to bypass WAFs/Cloudflare
        # -random-agent OR custom UA: user agent
        # -H Custom headers to bypass protections
        # -retries 2: retry failed requests
        # -timeout 10: reasonable timeout
        # -rl 150: rate limit to avoid detection
        httpx_cmd = f"""cat {live_subs_file} | httpx-toolkit \
            -silent \
            -json \
            {ua_option} \
            -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' \
            -H 'Accept-Language: en-US,en;q=0.5' \
            -H 'Accept-Encoding: gzip, deflate' \
            -H 'DNT: 1' \
            -H 'Connection: keep-alive' \
            -H 'Upgrade-Insecure-Requests: 1' \
            -retries 2 \
            -timeout 10 \
            -rl 150 \
            -o {httpx_json}"""
        
        try:
            result = subprocess.run(httpx_cmd, shell=True, capture_output=True, text=True, cwd=self.scan_dir)
            print(f"HTTPx completed with exit code: {result.returncode}")
            if result.stderr:
                print(f"HTTPx stderr: {result.stderr[:200]}")
                
            # Create simple URL list
            if os.path.exists(httpx_json):
                with open(alive_file, 'w') as outfile:
                    with open(httpx_json, 'r') as jsonfile:
                        for line in jsonfile:
                            try:
                                data = json.loads(line)
                                if 'url' in data:
                                    outfile.write(data['url'] + '\n')
                            except json.JSONDecodeError:
                                pass
                print(f"HTTPx: Created {alive_file}")
        except Exception as e:
            print(f"HTTPx error: {e}")
    
    def _run_gau(self):
        """Run GAU to extract URLs with stealth"""
        alive_file = os.path.join(self.scan_dir, "alive_webservices.txt")
        gau_output = os.path.join(self.scan_dir, "gau_urls.txt")
        
        self.logger.info("GAU: Starting URL extraction")
        
        if not os.path.exists(alive_file):
            self.logger.error(f"GAU: {alive_file} not found")
            return
            
        if os.path.getsize(alive_file) == 0:
            self.logger.error(f"GAU: {alive_file} is empty")
            return
        
        # Read URLs from alive_webservices.txt and extract domains
        domains = set()
        try:
            with open(alive_file, 'r') as f:
                for line in f:
                    url = line.strip()
                    if url:
                        # Extract domain from URL without port
                        from urllib.parse import urlparse
                        parsed = urlparse(url)
                        domain = parsed.netloc
                        if domain:
                            # Remove port if present (GAU doesn't handle ports)
                            domain = domain.split(':')[0]
                            domains.add(domain)
            self.logger.info(f"GAU: Processing {len(domains)} domains")
        except Exception as e:
            self.logger.error(f"Error reading alive_webservices: {e}")
            return
        
        # Use full path to gau
        gau_bin = os.path.expanduser("~/go/bin/gau")
        if not os.path.exists(gau_bin):
            gau_bin = "gau"  # Fallback to PATH
        
        # Build environment with custom user agent if rotation is enabled
        env = os.environ.copy()
        if self.rotate_user_agents:
            user_agent = self.get_random_user_agent()
            env['HTTP_USER_AGENT'] = user_agent
            self.logger.info(f"GAU: Using custom user agent rotation")
        
        # Run GAU on each domain with stealth settings
        # --blacklist: skip certain extensions
        # --threads: parallel processing
        # --timeout: avoid hanging
        # --providers: use multiple sources
        all_urls = set()
        for domain in domains:
            gau_cmd = f"echo {domain} | {gau_bin} --threads 5 --timeout 20 --blacklist ttf,woff,woff2,svg,eot --providers wayback,commoncrawl,otx,urlscan"
            try:
                self.logger.debug(f"GAU: Running for domain: {domain}")
                result = subprocess.run(
                    gau_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=self.scan_dir,
                    env=env
                )
                if result.stdout:
                    for url in result.stdout.strip().split('\n'):
                        if url.strip():
                            all_urls.add(url.strip())
                    self.logger.debug(f"GAU: Found {len(all_urls)} total URLs so far for {domain}")
                if result.stderr:
                    self.logger.debug(f"GAU stderr for {domain}: {result.stderr[:200]}")
            except Exception as e:
                self.logger.error(f"Error running GAU for {domain}: {e}")
                continue
        
        # Write results
        with open(gau_output, 'w') as f:
            for url in sorted(all_urls):
                f.write(f"{url}\n")
        
        self.logger.info(f"GAU: Total {len(all_urls)} URLs saved to {gau_output}")
        self.tools_status['gau']['count'] = len(all_urls)
    
    def _run_gospider(self):
        """Run gospider to extract URLs with stealth settings"""
        alive_file = os.path.join(self.scan_dir, "alive_webservices.txt")
        gospider_output = os.path.join(self.scan_dir, "gospider_urls.txt")
        
        self.logger.info("GoSpider: Starting URL extraction")
        
        if not os.path.exists(alive_file):
            self.logger.error(f"GoSpider: {alive_file} not found")
            return
            
        if os.path.getsize(alive_file) == 0:
            self.logger.error(f"GoSpider: {alive_file} is empty")
            return
        
        # Use full path to gospider
        gospider_bin = os.path.expanduser("~/go/bin/gospider")
        if not os.path.exists(gospider_bin):
            gospider_bin = "gospider"  # Fallback to PATH
        
        # Build user agent option
        if self.rotate_user_agents:
            user_agent = self.get_random_user_agent()
            ua_option = f"-H 'User-Agent: {user_agent}'"
            self.logger.info(f"GoSpider: Using custom user agent rotation")
        else:
            ua_option = "-u web"
        
        # Run gospider with stealth flags
        # -S: sites list file
        # -c: concurrent requests (lower to avoid detection)
        # -d: depth  
        # --sitemap --robots: crawl sitemap and robots.txt
        # -m: timeout in seconds
        # -q: quiet mode
        # -u web OR custom UA: user-agent
        # --blacklist: regex pattern to filter static files
        # -a: enable other sources (Archive.org, CommonCrawl, etc.)
        gospider_cmd = f"{gospider_bin} -S {alive_file} -c 5 -d 3 --sitemap --robots -m 20 -q {ua_option} --blacklist '\\.(css|png|jpeg|jpg|svg|img|gif|mp4|flv|ogv|webm|webp|woff|woff2|ttf|eot|otf|ico)$' -a"
        
        try:
            self.logger.debug(f"GoSpider: Running command: {gospider_cmd}")
            result = subprocess.run(
                gospider_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes timeout (gospider can be slow)
                cwd=self.scan_dir
            )
            
            self.logger.info(f"GoSpider completed with exit code: {result.returncode}")
            if result.stderr:
                self.logger.debug(f"GoSpider stderr: {result.stderr[:500]}")
            
            # Parse gospider output (format: [url_type] - url)
            urls = set()
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        # Extract URL from gospider format: [type] - url
                        if ' - ' in line:
                            parts = line.split(' - ', 1)
                            if len(parts) >= 2:
                                url = parts[1].strip()
                                if url and url.startswith('http'):
                                    urls.add(url)
                        # Also handle simple URL lines
                        elif line.strip().startswith('http'):
                            urls.add(line.strip())
            
            # Write results
            with open(gospider_output, 'w') as f:
                for url in sorted(urls):
                    f.write(f"{url}\n")
            
            self.logger.info(f"GoSpider: Total {len(urls)} URLs saved to {gospider_output}")
            self.tools_status['gospider']['count'] = len(urls)
        except Exception as e:
            self.logger.error(f"Error running gospider: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _run_merge2(self):
        """Merge all URLs from httpx, GAU, and gospider"""
        all_urls = set()
        
        # Files to merge
        url_files = [
            os.path.join(self.scan_dir, "alive_webservices.txt"),
            os.path.join(self.scan_dir, "gau_urls.txt"),
            os.path.join(self.scan_dir, "gospider_urls.txt")
        ]
        
        for filepath in url_files:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            url = line.strip()
                            if url:
                                all_urls.add(url)
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
        
        # Save merged URLs
        merged_file = os.path.join(self.scan_dir, "all_urls_merged.txt")
        with open(merged_file, 'w') as f:
            for url in sorted(all_urls):
                f.write(f"{url}\n")
        
        self.tools_status['merge2']['count'] = len(all_urls)
        return len(all_urls)
    
    def run_gowitness(self):
        """Run gowitness to capture screenshots with stealth settings"""
        alive_file = os.path.join(self.scan_dir, "all_urls_merged.txt")
        
        self.logger.info("GoWitness: Starting screenshot capture")
        
        if not os.path.exists(alive_file):
            self.logger.error(f"GoWitness: {alive_file} not found")
            return
            
        if os.path.getsize(alive_file) == 0:
            self.logger.error(f"GoWitness: {alive_file} is empty")
            return
        
        # Count URLs
        with open(alive_file, 'r') as f:
            url_count = sum(1 for line in f if line.strip())
        self.logger.info(f"GoWitness: Processing {url_count} URLs")
        
        # Create screenshots directory for this scan
        scan_screenshots_dir = os.path.join(self.screenshots_dir, self.scan_id)
        os.makedirs(scan_screenshots_dir, exist_ok=True)
        
        gowitness_db = os.path.join(self.scan_dir, "gowitness.sqlite3")
        
        # Use full path to gowitness
        gowitness_bin = os.path.expanduser("~/go/bin/gowitness")
        if not os.path.exists(gowitness_bin):
            gowitness_bin = "gowitness"  # Fallback to PATH
            self.logger.debug(f"GoWitness: Using PATH fallback for gowitness binary")
        
        # Select user agent
        if self.rotate_user_agents:
            user_agent = self.get_random_user_agent()
            self.logger.info(f"GoWitness: Using custom user agent rotation")
        else:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        
        # GoWitness with stealth flags
        # --screenshot-path: where to save screenshots
        # --write-db: output to SQLite database (needed for results)
        # --delay: delay between requests  
        # --timeout: timeout for page load
        # --threads: parallel processing
        # --chrome-user-agent: custom user agent  
        gowitness_cmd = (
            f"{gowitness_bin} scan file -f {alive_file} "
            f"--threads 10 "
            f"--delay 3 "
            f"--timeout 30 "
            f"--screenshot-path {scan_screenshots_dir}/ "
            f"--write-db "
            f"--write-db-uri sqlite://{gowitness_db} "
            f"--chrome-user-agent '{user_agent}'"
        )
        
        chrome_path = self.get_chrome_path()
        if chrome_path:
            gowitness_cmd += f' --chrome-path "{chrome_path}"'
            self.logger.debug(f"GoWitness: Using Chrome at {chrome_path}")
        
        try:
            self.logger.debug(f"GoWitness: Running command (truncated): {gowitness_cmd[:200]}...")
            result = subprocess.run(
                gowitness_cmd,
                shell=True,
                capture_output=True,
                cwd=self.scan_dir,
                text=True,
                timeout=600  # 10 minutes max
            )
            self.logger.info(f"GoWitness completed with exit code: {result.returncode}")
            if result.stdout:
                self.logger.debug(f"GoWitness stdout: {result.stdout[:500]}")
            if result.stderr:
                self.logger.debug(f"GoWitness stderr: {result.stderr[:500]}")
                
            # Check if screenshots were created
            if os.path.exists(scan_screenshots_dir):
                screenshots = [f for f in os.listdir(scan_screenshots_dir) if f.endswith('.png')]
                self.logger.info(f"GoWitness: Created {len(screenshots)} screenshot files")
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"GoWitness timed out after 10 minutes")
        except Exception as e:
            self.logger.error(f"GoWitness error: {e}")
    
    def parse_results(self):
        """Parse all results"""
        # Parse URLs from merged file
        merged_file = os.path.join(self.scan_dir, "all_urls_merged.txt")
        if os.path.exists(merged_file):
            with open(merged_file, 'r') as f:
                for line in f:
                    url = line.strip()
                    if url:
                        self.urls.append({'url': url, 'status_code': None})
        
        # Parse gowitness database for screenshots
        gowitness_db = os.path.join(self.scan_dir, "gowitness.sqlite3")
        if os.path.exists(gowitness_db):
            try:
                conn = sqlite3.connect(gowitness_db)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                rows = cursor.execute(
                    'SELECT url, final_url, response_code, response_code_text, title, filename FROM urls'
                ).fetchall()
                
                for row in rows:
                    self.screenshots.append({
                        'url': row['url'] or row['final_url'],
                        'status_code': row['response_code'],
                        'title': row['title'],
                        'filename': os.path.join(self.scan_id, row['filename']),
                        'headers': {}
                    })
                
                # Update URLs with status codes
                for url_data in self.urls:
                    for screenshot in self.screenshots:
                        if url_data['url'] in screenshot['url'] or screenshot['url'] in url_data['url']:
                            url_data['status_code'] = screenshot['status_code']
                            break
                
                conn.close()
            except Exception as e:
                print(f"Error parsing gowitness database: {e}")
    
    def cleanup(self):
        """Clean up temporary files"""
        # Note: We keep .txt files until the full scan is complete
        # They will be deleted by cleanup_txt_files()
        pass
    
    def cleanup_txt_files(self):
        """Delete all residual .txt files after scan completion"""
        for filepath in self.temp_files:
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"Deleted: {filepath}")
                except OSError as e:
                    print(f"Error deleting {filepath}: {e}")
        
        # Also delete the scan directory gowitness database
        gowitness_db = os.path.join(self.scan_dir, "gowitness.sqlite3")
        if os.path.exists(gowitness_db):
            try:
                os.remove(gowitness_db)
                print(f"Deleted: {gowitness_db}")
            except OSError as e:
                print(f"Error deleting gowitness db: {e}")
