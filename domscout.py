#!/usr/bin/env python3
import subprocess
import sys
import os
import threading
import time
import argparse
import concurrent.futures
import platform
import shutil

class ProgressLoader:
    def __init__(self, total_steps):
        self.total_steps = total_steps
        self.current_step = 0
        self.desc = ""
        self.stop_event = threading.Event()
        self.thread = None
        self.local_progress = 0.0

    def _animate(self):
        chars = "/-\\|"
        i = 0
        while not self.stop_event.is_set():
            time.sleep(0.1)
            
            if self.current_step > 0 and self.current_step <= self.total_steps:
                if self.local_progress < 0.95:
                    self.local_progress += (0.95 - self.local_progress) * 0.05
                
                base_percent = (self.current_step - 1) / self.total_steps
                step_fraction = 1 / self.total_steps
                current_total_fraction = base_percent + (self.local_progress * step_fraction)
            elif self.current_step > self.total_steps:
                current_total_fraction = 1.0
            else:
                current_total_fraction = 0.0

            percent_val = current_total_fraction * 100
            bar_len = 40
            filled = int(bar_len * current_total_fraction)
            bar = "█" * filled + "-" * (bar_len - filled)
            
            char = chars[i % len(chars)]
            
            sys.stdout.write(f"\r{char} [{bar}] {percent_val:.1f}% {self.desc}\033[K")
            sys.stdout.flush()
            i += 1

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._animate)
        self.thread.start()

    def update(self, step, desc):
        self.current_step = step
        self.desc = desc
        self.local_progress = 0.0

    def finish(self, desc="Completed!"):
        self.current_step = self.total_steps + 1 # Force 100%
        self.desc = desc
        # Allow one render cycle to show 100%
        time.sleep(0.2)
        self.stop()

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join()
        sys.stdout.write("\n")

def get_chrome_path():
    """Attempt to locate the Google Chrome binary."""
    system = platform.system()
    if system == "Darwin":
        # Check standard paths
        paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
        ]
        for path in paths:
            if os.path.exists(path):
                return path
        
        # Try mdfind as a fallback
        try:
            out = subprocess.check_output(["mdfind", "kMDItemDisplayName == 'Google Chrome'"], stderr=subprocess.DEVNULL).decode().strip()
            if out:
                lines = out.split('\n')
                for line in lines:
                    if line.endswith(".app"):
                        path = os.path.join(line, "Contents/MacOS/Google Chrome")
                        if os.path.exists(path):
                            return path
        except:
            pass
            
    elif system == "Linux":
        # Check common linux paths
        paths = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]
        for path in paths:
            if shutil.which(path):
                return shutil.which(path)
                
    return None

def run_command(command, description):
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass

def cleanup_files(filenames, include_artifacts=False):
    """Clean up temporary files."""
    files_to_remove = filenames + ["subdomains.txt"]
    if include_artifacts:
        files_to_remove.append("gowitness.sqlite3")
        files_to_remove.append("alive_webservices.txt")
        files_to_remove.append("live_subs.txt")

    for filename in files_to_remove:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                pass
    
    if include_artifacts and os.path.exists("screenshots"):
        try:
            shutil.rmtree("screenshots")
        except OSError:
            pass

def print_banner():
    print(r"""
  ____                  ____                   _       ,_,
 |  _ \  ___  _ __ ___ / ___|  ___ ___  _   _| |_     (O,O)
 | | | |/ _ \| '_ ` _ \\___ \ / __/ _ \| | | | __|    (   )
 | |_| | (_) | | | | | |___) | (_| (_) | |_| | |_     -"-"-
 |____/ \___/|_| |_| |_|____/ \___\___/ \__,_|\__|
                                                  """)
    print(" Author: julichaan")
    print(" Version: 1.0")
    print("-" * 50)

def main():
    print_banner()
    
    # Check for opendb command
    if len(sys.argv) > 1 and sys.argv[1] == "opendb":
        if not os.path.exists("gowitness.sqlite3"):
            print("[!] Error: 'gowitness.sqlite3' database not found.")
            print("    Run a scan first (and ensure artifacts are kept if you modified the script).")
            sys.exit(1)
        
        print("[*] Starting gowitness report server...")
        print("    [>] Access the report at: http://localhost:7171")
        print("    [!] Press Ctrl+C to stop the server.")
        try:
            subprocess.run("gowitness report server", shell=True)
        except KeyboardInterrupt:
            print("\n[!] Server stopped.")
        sys.exit(0)

    parser = argparse.ArgumentParser(description="DomScout - Subdomain Enumeration Tool")
    parser.add_argument("target", help="Target domain (e.g., example.com)")
    parser.add_argument("-r", "--resolvers", required=True, help="Path to resolvers file")
    parser.add_argument("-rl", "--rate-limit", type=int, default=150, help="Rate limit for httpx (requests per second)")
    
    args = parser.parse_args()
    
    target = args.target
    resolvers = args.resolvers
    rate_limit = args.rate_limit

    if not os.path.exists(resolvers):
        print(f"[!] Error: Resolvers file not found at {resolvers}")
        sys.exit(1)

    if os.path.getsize(resolvers) == 0:
        print(f"[!] Error: Resolvers file at {resolvers} is empty.")
        sys.exit(1)
    
    filenames = ["subfinder-rescursive.txt", "findomain.txt", "assetfinder.txt", "sublist3r.txt"]
    
    commands = [
        (f"subfinder -d {target} -all -silent -o subfinder-rescursive.txt", "subfinder"),
        (f"findomain --quiet -t {target} > findomain.txt", "findomain"),
        (f"assetfinder -subs-only {target} > assetfinder.txt", "assetfinder"),
        (f"sublist3r -d {target} -t 50 -o sublist3r.txt", "sublist3r")
    ]

    total_steps = len(commands) + 5 
    current_step = 0

    print(f"[*] Starting enumeration for: {target}")
    
    loader = ProgressLoader(total_steps)
    loader.start()
    
    try:
        loader.update(current_step, "Starting parallel enumeration...")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_desc = {executor.submit(run_command, cmd, desc): desc for cmd, desc in commands}
            
            for future in concurrent.futures.as_completed(future_to_desc):
                desc = future_to_desc[future]
                current_step += 1
                loader.update(current_step, f"Finished {desc}")
                try:
                    future.result()
                except Exception:
                    pass

        current_step += 1
        loader.update(current_step, "Processing results...")
        
        unique_subdomains = set()

        for filename in filenames:
            if os.path.exists(filename):
                try:
                    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            clean_line = line.strip()
                            if clean_line:
                                unique_subdomains.add(clean_line)
                except Exception:
                    pass

        with open("subdomains.txt", "w") as f:
            for subdomain in sorted(unique_subdomains):
                f.write(f"{subdomain}\n")
        
        count = len(unique_subdomains)
        print(f"[*] Found {count} unique subdomains. Saving to subdomains.txt...")

        if count == 0:
            loader.stop()
            print("[!] No subdomains found. Exiting.")
            sys.exit(0)

        current_step += 1
        loader.update(current_step, "Running dnsx...")

        resolvers_abs = os.path.abspath(resolvers)
        dnsx_cmd = f"dnsx -l subdomains.txt -r {resolvers_abs} -o live_subs.txt"
        
        # Capture stderr for better debugging
        process = subprocess.run(dnsx_cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        
        if process.returncode != 0:
            loader.stop()
            print(f"\n[!] Error running dnsx (Exit Code: {process.returncode}).")
            if process.stderr:
                print(f"    Details: {process.stderr.strip()}")
            else:
                print("    Verify that dnsx is installed and the resolvers list is valid.")
            sys.exit(1)
        
        if not os.path.exists("live_subs.txt") or os.path.getsize("live_subs.txt") == 0:
            loader.stop()
            print("[!] dnsx did not resolve any subdomains. 'live_subs.txt' is empty.")
            print(f"    - Check if your resolvers file ({resolvers}) contains valid DNS servers.")
            print("    - Try running dnsx manually to debug: " + dnsx_cmd)
            sys.exit(0)
        
        current_step += 1
        loader.update(current_step, "Running httpx (sudo)...")
        

        httpx_cmd = f"cat live_subs.txt | httpx-toolkit -rl {rate_limit} > alive_webservices.txt"
        try:
            subprocess.run(httpx_cmd, shell=True, check=True)
        except subprocess.CalledProcessError:
            # Stop loader to print error cleanly
            loader.stop()
            print("\n[!] Error running httpx. Ensure you have sudo permissions or that httpx is installed.")
            sys.exit(1)

        current_step += 1
        
        # Count web services to give feedback
        web_count = 0
        if os.path.exists("alive_webservices.txt"):
            with open("alive_webservices.txt", "r") as f:
                web_count = sum(1 for line in f if line.strip())
                
        loader.stop() # Stop loader to show gowitness output
        print(f"[*] Taking screenshots of {web_count} services...")

        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")

        gowitness_cmd = "gowitness scan file -f alive_webservices.txt --threads 20 --delay 2 --timeout 20 --screenshot-path screenshots/ --write-db"
        
        chrome_path = get_chrome_path()
        if chrome_path:
            gowitness_cmd += f" --chrome-path \"{chrome_path}\""

        try:
            subprocess.run(gowitness_cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as e:
            print(f"\n[!] gowitness failed to run.")
            # Error handling continues...

        current_step += 1
        loader.update(current_step, "Cleaning up files...")
        
        cleanup_files(filenames)
        
        loader.finish()
        
        print(f"\n[+] Process finished.\n    - Resolved subdomains: 'live_subs.txt'\n    - Alive web services: 'alive_webservices.txt'\n    - Screenshots: './screenshots/'")

        print("\n[*] Starting gowitness report server...")
        print("    [>] Access the report at: http://localhost:7171")
        print("    [!] Press Ctrl+C to stop the server and exit.")
        
        try:
            subprocess.run("gowitness report server", shell=True)
        except KeyboardInterrupt:
            print("\n[!] Server stopped.")
        
        cleanup_files([], include_artifacts=False)

    except KeyboardInterrupt:
        loader.stop()
        print("\n\n[!] Interrupted by user. Cleaning up temporary files...")
        cleanup_files(filenames, include_artifacts=True)
        sys.exit(0)

if __name__ == "__main__":
    main()
