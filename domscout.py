#!/usr/bin/env python3
import subprocess
import sys
import os
import threading
import time
import argparse
import concurrent.futures

class ProgressLoader:
    def __init__(self, total_steps):
        self.total_steps = total_steps
        self.current_step = 0
        self.desc = ""
        self.stop_event = threading.Event()
        self.thread = None
        self.local_progress = 0.0

    def _animate(self):
        chars = "/-\|"
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

def run_command(command, description):
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
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
    
    parser = argparse.ArgumentParser(description="DomScout - Subdomain Enumeration Tool")
    parser.add_argument("target", help="Target domain (e.g., example.com)")
    
    args = parser.parse_args()
    
    target = args.target
    
    commands = [
        (f"subfinder -d {target} -all -silent -o subfinder-rescursive.txt", "subfinder"),
        (f"findomain --quiet -t {target} > findomain.txt", "findomain"),
        (f"assetfinder -subs-only {target} > assetfinder.txt", "assetfinder"),
        (f"sublist3r -d {target} -t 50 -o sublist3r.txt", "sublist3r"),
        (f'curl -s "https://crt.sh/?q=%25.{target}&output=json" | jq -r \'.[].name_value\' | sed \'s/\*\.//g\' > "crtsh.txt"', "crt.sh")
    ]

    total_steps = len(commands) + 3 
    current_step = 0

    print(f"[*] Starting enumeration for: {target}")
    
    loader = ProgressLoader(total_steps)
    loader.start()
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
    
    filenames = ["subfinder-rescursive.txt", "findomain.txt", "assetfinder.txt", "sublist3r.txt", "crtsh.txt"]
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
    loader.update(current_step, "Running httpx (sudo)...")
    

    httpx_cmd = "cat subdomains.txt | sudo httpx > alive_webservices.txt"
    try:
        subprocess.run(httpx_cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        # Stop loader to print error cleanly
        loader.stop()
        print("\n[!] Error running httpx. Ensure you have sudo permissions or that httpx is installed.")
        sys.exit(1)

    current_step += 1
    loader.update(current_step, "Cleaning up files...")
    
    files_to_remove = filenames + ["subdomains.txt"]
    for filename in files_to_remove:
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except OSError:
                pass
    
    loader.finish()
    
    print(f"\n[+] Process finished.\n    - Alive web services: 'alive_webservices.txt'")

if __name__ == "__main__":
    main()
