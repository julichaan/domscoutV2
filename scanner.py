#!/usr/bin/env python3
import subprocess
import os
import time
import concurrent.futures
import shutil
import platform
import json
import sqlite3


class DomScoutScanner:
    def __init__(self, scan_id, target, rate_limit, resolvers_file, screenshots_dir):
        self.scan_id = scan_id
        self.target = target
        self.rate_limit = rate_limit
        self.resolvers_file = resolvers_file
        self.screenshots_dir = screenshots_dir
        
        # Create scan-specific directory
        self.scan_dir = os.path.join(os.path.dirname(screenshots_dir), f'scan_{scan_id}')
        os.makedirs(self.scan_dir, exist_ok=True)
        
        # Results
        self.subdomains = []
        self.live_subdomains = []
        self.urls = []
        self.screenshots = []
        
        # Progress tracking
        self.total_steps = 6
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
            'crtsh': {'status': 'idle', 'count': 0},
            'merge': {'status': 'idle', 'count': 0},
            'dnsx': {'status': 'idle', 'count': 0},
            'httpx': {'status': 'idle', 'count': 0},
            'gowitness': {'status': 'idle', 'count': 0}
        }
        
        # Temp files
        self.temp_files = [
            os.path.join(self.scan_dir, "subfinder-rescursive.txt"),
            os.path.join(self.scan_dir, "findomain.txt"),
            os.path.join(self.scan_dir, "assetfinder.txt"),
            os.path.join(self.scan_dir, "sublist3r.txt"),
            os.path.join(self.scan_dir, "crtsh.txt"),
            os.path.join(self.scan_dir, "subdomains.txt"),
            os.path.join(self.scan_dir, "live_subs.txt"),
            os.path.join(self.scan_dir, "alive_webservices.txt")
        ]
    
    def update_progress(self, step, message):
        """Update scan progress"""
        self.current_step = step
        self.progress_message = message
        self.progress = (step / self.total_steps) * 100
    
    def run_command(self, command):
        """Run a shell command silently"""
        try:
            subprocess.run(
                command,
                shell=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=self.scan_dir
            )
        except subprocess.CalledProcessError:
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
    
    def get_tool_results(self, tool_name):
        """Get results from a specific tool"""
        results = []
        
        # Map tool names to their result files
        file_map = {
            'subfinder': 'subfinder-rescursive.txt',
            'findomain': 'findomain.txt',
            'assetfinder': 'assetfinder.txt',
            'sublist3r': 'sublist3r.txt',
            'crtsh': 'crtsh.txt',
            'merge': 'subdomains.txt',
            'dnsx': 'live_subs.txt',
            'httpx': 'alive_webservices.txt',
            'gowitness': 'alive_webservices.txt'  # Same as httpx for now
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
            elif tool_name == 'crtsh':
                self._run_crtsh()
            elif tool_name == 'merge':
                self._run_merge()
            elif tool_name == 'dnsx':
                self._run_dnsx_tool()
            elif tool_name == 'httpx':
                self._run_httpx_tool()
            elif tool_name == 'gowitness':
                self._run_gowitness_tool()
            
            self.tools_status[tool_name]['status'] = 'completed'
        except Exception as e:
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
    
    def _run_crtsh(self):
        """Run crt.sh query"""
        cmd = f'curl -s "https://crt.sh/?q=%25.{self.target}&output=json" | jq -r \'.[].name_value\' | sed \'s/\\*\\.//g\' > crtsh.txt'
        self.run_command(cmd)
        
        filepath = os.path.join(self.scan_dir, "crtsh.txt")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.tools_status['crtsh']['count'] = sum(1 for line in f if line.strip())
    
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
        
        # Parse URLs from httpx JSON output
        httpx_json = os.path.join(self.scan_dir, "httpx_output.json")
        if os.path.exists(httpx_json):
            self.urls = []  # Clear previous URLs
            try:
                with open(httpx_json, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            if 'url' in data:
                                self.urls.append({
                                    'url': data['url'],
                                    'status_code': data.get('status_code'),
                                    'title': data.get('title'),
                                    'content_length': data.get('content_length')
                                })
                        except json.JSONDecodeError:
                            pass
            except Exception as e:
                print(f"Error parsing httpx output: {e}")
            self.tools_status['httpx']['count'] = len(self.urls)
    
    def _run_gowitness_tool(self):
        """Run gowitness"""
        self.run_gowitness()
        
        # Parse and save screenshots
        gowitness_db = os.path.join(self.scan_dir, "gowitness.sqlite3")
        if os.path.exists(gowitness_db):
            try:
                conn = sqlite3.connect(gowitness_db)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                rows = cursor.execute(
                    'SELECT url, final_url, response_code, response_code_text, title, filename FROM urls'
                ).fetchall()
                
                # Clear previous screenshots for this scan
                self.screenshots = []
                
                for row in rows:
                    self.screenshots.append({
                        'url': row['url'] or row['final_url'],
                        'status_code': row['response_code'],
                        'title': row['title'],
                        'filename': os.path.join(self.scan_id, row['filename']),
                        'headers': {}
                    })
                
                self.tools_status['gowitness']['count'] = len(self.screenshots)
                conn.close()
            except Exception as e:
                print(f"Error parsing gowitness database: {e}")
    
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
            
            # Step 5: Take screenshots
            self.update_progress(5, "Taking screenshots with gowitness...")
            self.run_single_tool('gowitness')
            
            # Step 6: Parse results
            self.update_progress(6, "Processing results...")
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
        tools = ['subfinder', 'findomain', 'assetfinder', 'sublist3r', 'crtsh']
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.run_single_tool, tool) for tool in tools]
            concurrent.futures.wait(futures)
    
    def merge_subdomains(self):
        """Merge and deduplicate subdomains"""
        unique_subdomains = set()
        
        for filename in ["subfinder-rescursive.txt", "findomain.txt", "assetfinder.txt", "sublist3r.txt", "crtsh.txt"]:
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
        """Run httpx to find alive web services"""
        live_subs_file = os.path.join(self.scan_dir, "live_subs.txt")
        alive_file = os.path.join(self.scan_dir, "alive_webservices.txt")
        httpx_json = os.path.join(self.scan_dir, "httpx_output.json")
        
        if not os.path.exists(live_subs_file) or os.path.getsize(live_subs_file) == 0:
            return
        
        # Run httpx with JSON output to capture status codes
        httpx_cmd = f"cat {live_subs_file} | httpx-toolkit -rl {self.rate_limit} -silent -status-code -json -o {httpx_json}"
        
        try:
            subprocess.run(httpx_cmd, shell=True, check=True, cwd=self.scan_dir)
            
            # Also create simple URL list for gowitness
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
        except subprocess.CalledProcessError:
            pass
    
    def run_gowitness(self):
        """Run gowitness to capture screenshots"""
        alive_file = os.path.join(self.scan_dir, "alive_webservices.txt")
        
        if not os.path.exists(alive_file) or os.path.getsize(alive_file) == 0:
            return
        
        # Create screenshots directory for this scan
        scan_screenshots_dir = os.path.join(self.screenshots_dir, self.scan_id)
        os.makedirs(scan_screenshots_dir, exist_ok=True)
        
        gowitness_db = os.path.join(self.scan_dir, "gowitness.sqlite3")
        
        # Use full path to gowitness
        gowitness_bin = os.path.expanduser("~/go/bin/gowitness")
        if not os.path.exists(gowitness_bin):
            gowitness_bin = "gowitness"  # Fallback to PATH
        
        gowitness_cmd = (
            f"{gowitness_bin} scan file -f {alive_file} "
            f"--threads 20 --delay 2 --timeout 20 "
            f"--screenshot-path {scan_screenshots_dir}/ "
            f"--db-path {gowitness_db}"
        )
        
        chrome_path = self.get_chrome_path()
        if chrome_path:
            gowitness_cmd += f' --chrome-path "{chrome_path}"'
        
        try:
            result = subprocess.run(
                gowitness_cmd,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.scan_dir,
                text=True
            )
            print(f"GoWitness completed successfully")
            if result.stdout:
                print(f"GoWitness output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            print(f"GoWitness error (exit code {e.returncode}): {error_msg}")
            if e.stdout:
                print(f"GoWitness stdout: {e.stdout}")
    
    def parse_results(self):
        """Parse all results"""
        # Parse URLs
        alive_file = os.path.join(self.scan_dir, "alive_webservices.txt")
        if os.path.exists(alive_file):
            with open(alive_file, 'r') as f:
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
