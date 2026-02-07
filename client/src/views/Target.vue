<template>
  <div class="target-view">
    <div class="container">
      <!-- Target Header -->
      <div class="target-header card">
        <button class="btn btn-secondary btn-back" @click="goBack">
          ← Back
        </button>
        <div class="target-info">
          <h1>{{ target }}</h1>
          <span class="target-type">Wildcard Target</span>
        </div>
        <button 
          class="btn btn-primary btn-auto-scan"
          @click="runAutoScan"
          :disabled="isAutoScanning"
        >
          <span v-if="!isAutoScanning">🚀 Auto Scan All</span>
          <span v-else>
            <span class="spinner-small"></span> Scanning...
          </span>
        </button>
      </div>

      <!-- Tools Grid -->
      <div class="tools-section">
        <h2>Enumeration Tools</h2>
        <p class="section-description">Run individual tools or use Auto Scan to run all tools sequentially</p>
        
        <div class="tools-grid">
          <!-- Tool Card: Subfinder -->
          <ToolCard
            title="Subfinder"
            description="Fast subdomain enumeration using passive sources"
            :status="tools.subfinder.status"
            :count="tools.subfinder.count"
            @run="runTool('subfinder')"
            @view-results="viewToolResults('subfinder')"
          />

          <!-- Tool Card: Findomain -->
          <ToolCard
            title="Findomain"
            description="Comprehensive subdomain discovery"
            :status="tools.findomain.status"
            :count="tools.findomain.count"
            @run="runTool('findomain')"
            @view-results="viewToolResults('findomain')"
          />

          <!-- Tool Card: Assetfinder -->
          <ToolCard
            title="Assetfinder"
            description="Find domains and subdomains"
            :status="tools.assetfinder.status"
            :count="tools.assetfinder.count"
            @run="runTool('assetfinder')"
            @view-results="viewToolResults('assetfinder')"
          />

          <!-- Tool Card: Sublist3r -->
          <ToolCard
            title="Sublist3r"
            description="Subdomain enumeration using search engines"
            :status="tools.sublist3r.status"
            :count="tools.sublist3r.count"
            @run="runTool('sublist3r')"
            @view-results="viewToolResults('sublist3r')"
          />

          <!-- Tool Card: crt.sh -->
          <ToolCard
            title="crt.sh"
            description="Certificate transparency logs"
            :status="tools.crtsh.status"
            :count="tools.crtsh.count"
            @run="runTool('crtsh')"
            @view-results="viewToolResults('crtsh')"
          />

          <!-- Tool Card: Merge -->
          <ToolCard
            title="Merge"
            description="Consolidate and deduplicate all subdomains"
            :status="tools.merge.status"
            :count="tools.merge.count"
            @run="runTool('merge')"
            @view-results="viewToolResults('merge')"
            :disabled="!hasEnumerationResults"
          />

          <!-- Tool Card: DNSx -->
          <ToolCard
            title="DNSx"
            description="Resolve live subdomains"
            :status="tools.dnsx.status"
            :count="tools.dnsx.count"
            @run="runTool('dnsx')"
            @view-results="viewToolResults('dnsx')"
            :disabled="!hasMergeResults"
          />

          <!-- Tool Card: HTTPx -->
          <ToolCard
            title="HTTPx"
            description="Probe for live web services"
            :status="tools.httpx.status"
            :count="tools.httpx.count"
            @run="runTool('httpx')"
            @view-results="viewToolResults('httpx')"
            :disabled="!hasLiveSubdomains"
          />

          <!-- Tool Card: GoWitness -->
          <ToolCard
            title="GoWitness"
            description="Screenshot web applications"
            :status="tools.gowitness.status"
            :count="tools.gowitness.count"
            @run="runTool('gowitness')"
            @view-results="viewToolResults('gowitness')"
            :disabled="!hasAliveUrls"
          />
        </div>
      </div>

      <!-- Show Results Button -->
      <div v-if="scanComplete" class="show-results-section">
        <button class="btn btn-primary btn-large" @click="viewResults">
          📊 Show Results
        </button>
      </div>

      <!-- Results Modal -->
      <div v-if="showResultsModal" class="modal" @click="closeResultsModal">
        <div class="modal-content" @click.stop>
          <button class="modal-close" @click="closeResultsModal">×</button>
          <h3>{{ selectedTool }} Results</h3>
          <div class="modal-search">
            <input
              v-model="resultSearch"
              type="text"
              class="input-field"
              placeholder="Search results..."
            />
          </div>
          <div class="results-list">
            <div
              v-for="(result, index) in filteredResults"
              :key="index"
              class="result-item"
            >
              {{ result }}
            </div>
            <div v-if="filteredResults.length === 0" class="no-results">
              No results found
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import ToolCard from '../components/ToolCard.vue'

export default {
  name: 'TargetView',
  components: {
    ToolCard
  },
  data() {
    return {
      target: '',
      scanId: null,
      isAutoScanning: false,
      tools: {
        subfinder: { status: 'idle', count: 0 },
        findomain: { status: 'idle', count: 0 },
        assetfinder: { status: 'idle', count: 0 },
        sublist3r: { status: 'idle', count: 0 },
        crtsh: { status: 'idle', count: 0 },
        merge: { status: 'idle', count: 0 },
        dnsx: { status: 'idle', count: 0 },
        httpx: { status: 'idle', count: 0 },
        gowitness: { status: 'idle', count: 0 }
      },
      pollInterval: null,
      showResultsModal: false,
      selectedTool: '',
      toolResults: [],
      resultSearch: ''
    }
  },
  computed: {
    hasEnumerationResults() {
      return this.tools.subfinder.count > 0 || 
             this.tools.findomain.count > 0 || 
             this.tools.assetfinder.count > 0 ||
             this.tools.sublist3r.count > 0 ||
             this.tools.crtsh.count > 0
    },
    hasMergeResults() {
      return this.tools.merge.count > 0
    },
    hasLiveSubdomains() {
      return this.tools.dnsx.count > 0
    },
    hasAliveUrls() {
      return this.tools.httpx.count > 0
    },
    scanComplete() {
      return this.tools.gowitness.status === 'completed'
    },
    filteredResults() {
      if (!this.resultSearch) return this.toolResults
      const search = this.resultSearch.toLowerCase()
      return this.toolResults.filter(r => r.toLowerCase().includes(search))
    }
  },
  mounted() {
    this.target = this.$route.params.target
    this.scanId = this.$route.params.scanId
    this.loadToolStatus()
    this.startPolling()
  },
  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval)
    }
  },
  methods: {
    async loadToolStatus() {
      if (!this.scanId) return
      
      try {
        const response = await axios.get(`/api/scan/${this.scanId}/tools`)
        this.tools = response.data.tools
        
        // Check if auto scan has completed
        if (this.isAutoScanning) {
          const allIdle = Object.values(this.tools).every(
            tool => tool.status === 'idle' || tool.status === 'completed' || tool.status === 'failed'
          )
          const anyRunning = Object.values(this.tools).some(tool => tool.status === 'running')
          
          // If nothing is running anymore, auto scan is done
          if (allIdle || !anyRunning) {
            // Check if the last tool (gowitness) is completed
            if (this.tools.gowitness.status === 'completed' || this.tools.gowitness.status === 'failed') {
              this.isAutoScanning = false
            }
          }
        }
      } catch (err) {
        console.error('Failed to load tool status:', err)
      }
    },
    async runTool(toolName) {
      try {
        this.tools[toolName].status = 'running'
        
        const response = await axios.post(`/api/scan/${this.scanId}/tool/${toolName}`)
        
        if (response.data.success) {
          // Tool started successfully
        }
      } catch (err) {
        this.tools[toolName].status = 'failed'
        console.error(`Failed to run ${toolName}:`, err)
      }
    },
    async runAutoScan() {
      this.isAutoScanning = true
      
      try {
        await axios.post(`/api/scan/${this.scanId}/auto`)
      } catch (err) {
        console.error('Failed to start auto scan:', err)
        this.isAutoScanning = false
      }
    },
    async viewToolResults(toolName) {
      try {
        const response = await axios.get(`/api/scan/${this.scanId}/tool/${toolName}/results`)
        this.toolResults = response.data.results
        this.selectedTool = toolName.charAt(0).toUpperCase() + toolName.slice(1)
        this.showResultsModal = true
        this.resultSearch = ''
      } catch (err) {
        console.error(`Failed to load ${toolName} results:`, err)
      }
    },
    closeResultsModal() {
      this.showResultsModal = false
      this.toolResults = []
      this.selectedTool = ''
      this.resultSearch = ''
    },
    startPolling() {
      this.pollInterval = setInterval(() => {
        this.loadToolStatus()
      }, 2000)
    },
    goBack() {
      this.$router.push('/')
    },
    viewResults() {
      this.$router.push(`/results/${this.scanId}`)
    }
  }
}
</script>

<style scoped>
.target-view {
  min-height: 100vh;
  padding: 40px 20px;
}

.target-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 40px;
  padding: 30px;
}

.btn-back {
  white-space: nowrap;
}

.target-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.target-info h1 {
  font-size: 32px;
  margin: 0;
  color: var(--accent-primary);
  word-break: break-all;
}

.target-type {
  font-size: 14px;
  color: var(--text-secondary);
  background: var(--bg-tertiary);
  padding: 4px 12px;
  border-radius: 12px;
  display: inline-block;
  width: fit-content;
}

.btn-auto-scan {
  font-size: 16px;
  padding: 14px 28px;
  white-space: nowrap;
}

.tools-section {
  margin-bottom: 40px;
}

.tools-section h2 {
  font-size: 28px;
  margin-bottom: 10px;
}

.section-description {
  color: var(--text-secondary);
  margin-bottom: 30px;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 20px;
}

.results-section {
  margin-top: 40px;
}

.results-section h2 {
  font-size: 28px;
  margin-bottom: 20px;
}

.results-actions {
  display: flex;
  gap: 15px;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Show Results Section */
.show-results-section {
  margin-top: 40px;
  text-align: center;
  padding: 40px 20px;
  background: var(--bg-secondary);
  border: 2px solid var(--accent-primary);
  border-radius: 12px;
  animation: fadeIn 0.5s ease;
}

.btn-large {
  font-size: 18px;
  padding: 16px 48px;
  min-width: 200px;
}

/* Modal Styles */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.3s ease;
}

.modal-content {
  max-width: 800px;
  width: 100%;
  max-height: 80vh;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 30px;
  position: relative;
  display: flex;
  flex-direction: column;
}

.modal-close {
  position: absolute;
  top: 20px;
  right: 20px;
  background: var(--bg-tertiary);
  border: none;
  color: var(--text-primary);
  font-size: 30px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.modal-close:hover {
  background: var(--accent-primary);
  color: white;
}

.modal-content h3 {
  margin-bottom: 20px;
  font-size: 24px;
  color: var(--accent-primary);
}

.modal-search {
  margin-bottom: 20px;
}

.results-list {
  flex: 1;
  overflow-y: auto;
  max-height: 500px;
}

.result-item {
  padding: 12px 16px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  margin-bottom: 8px;
  font-family: monospace;
  font-size: 14px;
  color: var(--text-primary);
  word-break: break-all;
  transition: all 0.2s ease;
}

.result-item:hover {
  border-color: var(--accent-primary);
  background: var(--bg-primary);
}

.no-results {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary);
  font-size: 16px;
}

@media (max-width: 768px) {
  .target-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .btn-auto-scan {
    width: 100%;
  }
  
  .tools-grid {
    grid-template-columns: 1fr;
  }
  
  .btn-large {
    width: 100%;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
