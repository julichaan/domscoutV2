import shutil
import subprocess
import sys
import platform
import os

TOOLS = [
    "subfinder",
    "findomain",
    "assetfinder",
    "sublist3r",
    "httpx",
    "curl",
    "jq"
]

def check_tool(tool):
    """Check if a tool is available in the system PATH."""
    return shutil.which(tool) is not None

def install_brew_tool(package_name):
    """Install a tool using Homebrew on macOS."""
    print(f"[*] Installing {package_name} via Homebrew...")
    try:
        subprocess.run(["brew", "install", package_name], check=True)
    except subprocess.CalledProcessError:
        print(f"[!] Failed to install {package_name} with brew. Trying to tap projectdiscovery if applicable...")
        if package_name in ["subfinder", "httpx"]:
             subprocess.run(["brew", "tap", "projectdiscovery/tap"], check=False)
             subprocess.run(["brew", "install", f"projectdiscovery/tap/{package_name}"], check=False)

def install_apt_tool(package_name):
    """Install a tool using apt on Linux."""
    print(f"[*] Installing {package_name} via apt...")
    subprocess.run(["sudo", "apt", "update"], check=False)
    subprocess.run(["sudo", "apt", "install", "-y", package_name], check=True)

def install_go_tool(package_url, binary_name):
    """Install a tool using Go."""
    print(f"[*] Installing {binary_name} via Go...")
    try:
        subprocess.run(["go", "install", package_url], check=True)
        
        # Check if GOPATH/bin is in PATH
        home = os.path.expanduser("~")
        go_bin = os.path.join(home, "go", "bin")
        if go_bin not in os.environ["PATH"]:
            print(f"[!] Warning: {go_bin} is not in your PATH. You may need to add it to run {binary_name}.")
            print(f"    export PATH=$PATH:{go_bin}")
    except Exception as e:
        print(f"[!] Failed to install {binary_name} via Go: {e}")

def install_pip_tool(package_name):
    """Install a tool using pip."""
    print(f"[*] Installing {package_name} via pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", package_name], check=True)

def install_linux_binary(url, binary_name):
    """Download and install a binary on Linux."""
    print(f"[*] Downloading binary for {binary_name}...")
    try:
        subprocess.run(f"curl -L -o {binary_name}.zip {url}", shell=True, check=True)
        subprocess.run(f"unzip -o {binary_name}.zip", shell=True, check=True)
        subprocess.run(f"chmod +x {binary_name}", shell=True, check=True)
        subprocess.run(f"sudo mv {binary_name} /usr/local/bin/", shell=True, check=True)
        subprocess.run(f"rm {binary_name}.zip", shell=True, check=False)
        print(f"[+] {binary_name} installed successfully.")
    except Exception as e:
        print(f"[!] Failed to install {binary_name}: {e}")

def main():
    system = platform.system()
    print(f"[*] Detected OS: {system}")

    if system == "Darwin":
        # macOS Installation
        if not check_tool("brew"):
            print("[!] Homebrew not found. Please install Homebrew first: https://brew.sh/")
            sys.exit(1)
        
        for tool in TOOLS:
            if check_tool(tool):
                print(f"[+] {tool} is already installed.")
                continue
            
            if tool in ["subfinder", "assetfinder", "httpx", "findomain", "curl", "jq"]:
                try:
                    install_brew_tool(tool)
                except Exception as e:
                    print(f"[!] Error installing {tool}: {e}")
            elif tool == "sublist3r":
                try:
                    install_pip_tool("sublist3r")
                except Exception as e:
                    print(f"[!] Error installing {tool}: {e}")

    elif system == "Linux":
        # Linux Installation
        has_apt = check_tool("apt")
        has_go = check_tool("go")

        for tool in TOOLS:
            if check_tool(tool):
                print(f"[+] {tool} is already installed.")
                continue

            if tool in ["curl", "jq"]:
                if has_apt:
                    try:
                        install_apt_tool(tool)
                    except:
                        print(f"[!] Failed to install {tool} via apt.")
                else:
                    print(f"[!] Package manager not supported. Please install {tool} manually.")
            
            elif tool == "sublist3r":
                try:
                    install_pip_tool("sublist3r")
                except:
                    print(f"[!] Failed to install {tool} via pip.")

            elif tool == "findomain":
                # Try to install findomain binary
                # Note: This URL is for x86_64 Linux. 
                url = "https://github.com/Findomain/Findomain/releases/latest/download/findomain-linux.zip"
                install_linux_binary(url, "findomain")

            elif tool in ["subfinder", "assetfinder", "httpx"]:
                if has_go:
                    url = ""
                    if tool == "subfinder": url = "github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest"
                    if tool == "assetfinder": url = "github.com/tomnomnom/assetfinder@latest"
                    if tool == "httpx": url = "github.com/projectdiscovery/httpx/cmd/httpx@latest"
                    install_go_tool(url, tool)
                else:
                    print(f"[!] Go is not installed. Cannot install {tool} automatically via Go.")
                    print(f"    Please install Go (https://go.dev/doc/install) or download the {tool} binary manually.")

    else:
        print(f"[!] Unsupported operating system: {system}. Please install tools manually.")

    print("\n[*] Installation check complete.")

if __name__ == "__main__":
    main()
