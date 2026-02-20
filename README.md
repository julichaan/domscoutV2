# DomScout v2

**Bug Bounty Subdomain Enumeration Framework with Web Interface**

DomScout v2 is a complete rewrite of the original DomScout tool, featuring a modern Vue.js web interface inspired by the [ars0n-framework-v2](https://github.com/R-s0n/ars0n-framework-v2). It aggregates results from multiple powerful reconnaissance tools and provides an intuitive interface for viewing screenshots, subdomain lists, and metadata.

```
  ____                  ____                   _       
 |  _ \  ___  _ __ ___ / ___|  ___ ___  _   _| |_     
 | | | |/ _ \| '_ ` _ \\___ \ / __/ _ \| | | | __|    
 | |_| | (_) | | | | | |___) | (_| (_) | |_| | |_     
 |____/ \___/|_| |_| |_|____/ \___\___/ \__,_|\__|    
                                             v2.0      
```

## 🌟 Features

- **Modern Web Interface**: Vue.js 3 frontend with real-time progress tracking
- **Multi-Tool Integration**: Combines results from `subfinder`, `findomain`, `assetfinder`, and `sublist3r`
- **Live Verification**: Uses `dnsx` and `httpx` to verify reachable subdomains and web services
- **Screenshot Gallery**: Captures screenshots of all live services with gowitness
- **Integrated Results Viewer**: Browse screenshots, metadata, and status codes directly in the web interface (no need for external gowitness server)
- **Scan History**: Track and review previous scans
- **Responsive Design**: Works on desktop and mobile devices

## 📋 Prerequisites

Before running DomScout v2, ensure you have the following installed:

### Required Software

- **Python 3.8+**: [Download Python](https://www.python.org/)
- **Node.js 16+**: [Download Node.js](https://nodejs.org/)
- **GNU Make**: usually preinstalled on Linux/macOS
- **Google Chrome**: Required for screenshots

### Required Tools

The following command-line tools must be installed and available in your PATH:

-   [Subfinder](https://github.com/projectdiscovery/subfinder) - Subdomain enumeration
-   [Findomain](https://github.com/Findomain/Findomain) - Subdomain discovery
-   [Assetfinder](https://github.com/tomnomnom/assetfinder) - Asset discovery
-   [Sublist3r](https://github.com/aboul3la/Sublist3r) - Subdomain enumeration
-   [DNSx](https://github.com/projectdiscovery/dnsx) - DNS resolution
-   [httpx](https://github.com/projectdiscovery/httpx) - HTTP probe (`httpx` / `httpx-toolkit` binary)
-   [gowitness](https://github.com/sensepost/gowitness) - Screenshot capture
-   `curl` - HTTP requests
-   `jq` - JSON processor

### Automated Installation

You can use the installer script directly:

```bash
python3 install.py
```

Or via Makefile:

```bash
make install-tools
```

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/julichaan/domscoutV2.git
cd domscoutV2
```

### 2. Run Setup (Recommended)

Use the Makefile:

```bash
make setup
```

This will:
- Create virtual environment (`venv`)
- Install backend Python dependencies
- Install frontend dependencies
- Build Vue frontend into `server/static`

### 3. Configure Subfinder (Recommended)

For best results, configure API keys for subfinder:

Edit `~/.config/subfinder/provider-config.yaml` and add your API keys for services like:
- SecurityTrails
- Censys
- Shodan
- VirusTotal
- etc.

See the [Subfinder documentation](https://github.com/projectdiscovery/subfinder#post-installation-instructions) for details.

## 🎯 Usage

### Start the Application

Recommended:

```bash
make start
```

The application will be available at **http://localhost:5000**

### Using the Web Interface

1. **Enter Target Domain**: Type your target domain (e.g., `example.com`)
2. **Configure Rate Limit**: Set the rate limit for httpx (default: 150 req/s)
3. **Click "Start Scan"**: The scan will begin automatically
4. **Monitor Progress**: Watch real-time progress as the scan runs
5. **View Results**: Once completed, browse:
   - **Screenshots Tab**: Gallery of captured screenshots with metadata
   - **Subdomains Tab**: Complete list of discovered subdomains
   - **URLs Tab**: Live web services with status codes

### Development Mode

For development with hot-reload:

```bash
make dev
```

- Backend: http://localhost:5000
- Frontend: http://localhost:8080

### Makefile Commands

```bash
make help           # List all targets
make install        # Tools + setup
make install-tools  # External recon tools
make setup          # App dependencies + build
make build          # Frontend build only
make start          # Start Flask (production style)
make dev            # Backend + Vue dev server
make status         # Quick environment/tool check
make clean          # Remove Python caches
make clean-db       # Remove SQLite database
make reset          # Full local cleanup
```

## 📁 Project Structure

```
domscoutV2/
├── client/                 # Vue.js frontend
│   ├── src/
│   │   ├── views/         # Page components
│   │   │   ├── Home.vue   # Main scan page
│   │   │   └── Results.vue # Results viewer
│   │   ├── router/        # Vue Router configuration
│   │   ├── assets/        # CSS and static assets
│   │   ├── App.vue        # Root component
│   │   └── main.js        # App entry point
│   ├── public/            # Static files
│   ├── package.json       # Node.js dependencies
│   └── vue.config.js      # Vue CLI configuration
│
├── server/                # Flask backend
│   ├── app.py            # Main Flask application
│   ├── requirements.txt  # Python dependencies
│   ├── domscout.db       # SQLite database (created on first run)
│   └── static/           # Built frontend (generated)
│
├── scanner.py            # Core scanning logic
├── domscout.py          # Original CLI tool (legacy)
├── Makefile             # Unified project management commands
├── install.py           # Tool installation script
├── resolvers.txt        # DNS resolvers list
├── screenshots/         # Screenshot storage
└── README.md           # This file
```

## 🔧 API Endpoints

The Flask backend provides the following REST API endpoints:

- `POST /api/scan` - Start a new scan
- `GET /api/scan/<scan_id>` - Get scan status and progress
- `GET /api/scan/<scan_id>/subdomains` - Get discovered subdomains
- `GET /api/scan/<scan_id>/urls` - Get live URLs
- `GET /api/scan/<scan_id>/screenshots` - Get screenshot metadata
- `GET /api/scans` - List all scans
- `GET /screenshots/<path>` - Serve screenshot files

## 🎨 Design Philosophy

DomScout v2 follows the design principles of the [ars0n-framework-v2](https://github.com/R-s0n/ars0n-framework-v2):

- **User-Focused Interface**: Clean, intuitive design that guides users through the workflow
- **Real-Time Feedback**: Progress bars and status updates keep users informed
- **Integrated Results**: No need to switch between terminal and browser
- **Modern Stack**: Vue.js 3, Flask, and SQLite for a lightweight yet powerful application

## 📊 How It Works

1. **Parallel Enumeration**: Runs 4 tools simultaneously (subfinder, findomain, assetfinder, sublist3r)
2. **Deduplication**: Merges and removes duplicate subdomains
3. **DNS Resolution**: Uses dnsx with custom resolvers to find live subdomains
4. **HTTP Probing**: httpx verifies which subdomains have active web services
5. **Screenshot Capture**: gowitness captures screenshots and metadata
6. **Temporary Workspace**: scan artifacts are generated in temporary directories during execution
7. **Database Storage**: final results are persisted in SQLite for querying/history
8. **Cleanup**: temporary scan artifacts are deleted after completion
9. **Web Display**: Vue.js frontend displays results in an intuitive interface

## 🛠️ Troubleshooting

### Frontend doesn't load
 
Build frontend assets first:

```bash
make build
```

### Scan fails immediately

Check that all required tools are installed:

```bash
which subfinder findomain assetfinder sublist3r dnsx httpx httpx-toolkit gowitness curl jq
```

### No subdomains found

- Verify your `resolvers.txt` contains valid DNS servers
- Check if the target domain is accessible
- Configure Subfinder API keys for better results

### Screenshots not working

- Ensure Google Chrome is installed
- Check gowitness installation: `gowitness version`

## 🆚 DomScout v1 vs v2

| Feature | v1 (CLI) | v2 (Web) |
|---------|----------|----------|
| Interface | Terminal | Web Browser |
| Progress Tracking | Text Animation | Real-time Progress Bar |
| Results Viewing | gowitness server | Integrated Web UI |
| Scan History | None | SQLite Database |
| Multiple Scans | Sequential | Tracked & Accessible |
| API | None | REST API |

## 📝 License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

## 👤 Author

**julichaan**

Inspired by [ars0n-framework-v2](https://github.com/R-s0n/ars0n-framework-v2) by rs0n

## 🙏 Acknowledgments

- rs0n for the ars0n-framework-v2 design inspiration
- ProjectDiscovery for subfinder, dnsx, and httpx
- All the amazing open-source tools that make this possible

---

**Happy Bug Bounty Hunting! 🎯🔍**
