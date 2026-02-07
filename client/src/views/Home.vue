<template>
  <div class="home">
    <div class="container">
      <div class="banner">
        <pre class="ascii-art">
  ____                  ____                   _       
 |  _ \  ___  _ __ ___ / ___|  ___ ___  _   _| |_     
 | | | |/ _ \| '_ ` _ \\___ \ / __/ _ \| | | | __|    
 | |_| | (_) | | | | | |___) | (_| (_) | |_| | |_     
 |____/ \___/|_| |_| |_|____/ \___\___/ \__,_|\__|    
                                             v2.0      
        </pre>
        <p class="subtitle">Bug Bounty Subdomain Enumeration Framework</p>
        <p class="author">by julichaan</p>
      </div>

      <div class="scan-section card fade-in">
        <h2>Start New Scan</h2>
        <p class="description">
          Enter a target domain to begin comprehensive subdomain enumeration
        </p>

        <div class="form-group">
          <label for="domain">Target Domain</label>
          <input
            id="domain"
            v-model="domain"
            type="text"
            class="input-field"
            placeholder="example.com"
            @keyup.enter="startScan"
            :disabled="isScanning"
          />
        </div>

        <div class="form-group">
          <label for="rateLimit">Rate Limit (requests/sec)</label>
          <input
            id="rateLimit"
            v-model="rateLimit"
            type="number"
            class="input-field"
            placeholder="150"
            :disabled="isScanning"
          />
        </div>

        <button
          class="btn btn-primary btn-scan"
          @click="startScan"
          :disabled="isScanning || !domain"
        >
          <span v-if="!isScanning">🔍 Start Scan</span>
          <span v-else class="scanning-text">
            <span class="spinner-small"></span> Scanning...
          </span>
        </button>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>
      </div>

      <div v-if="recentScans.length > 0" class="recent-scans card fade-in">
        <h3>Recent Scans</h3>
        <div class="scans-list">
          <div
            v-for="scan in recentScans"
            :key="scan.id"
            class="scan-item"
          >
            <div class="scan-content" @click="goToResults(scan)">
              <div class="scan-info">
                <span class="scan-domain">{{ scan.domain }}</span>
                <span class="scan-date">{{ formatDate(scan.created_at) }}</span>
              </div>
              <div class="scan-stats">
                <span class="stat">
                  <span class="stat-value">{{ scan.subdomains_count }}</span>
                  subdomains
                </span>
                <span class="stat">
                  <span class="stat-value">{{ scan.urls_count }}</span>
                  URLs
                </span>
              </div>
              <span class="scan-status" :class="scan.status">
                {{ scan.status }}
              </span>
            </div>
            <button
              class="btn-delete"
              @click.stop="deleteScan(scan.id)"
              title="Delete scan"
            >
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Home',
  data() {
    return {
      domain: '',
      rateLimit: 150,
      isScanning: false,
      error: null,
      recentScans: []
    }
  },
  mounted() {
    this.loadRecentScans()
  },
  methods: {
    async startScan() {
      if (!this.domain || this.isScanning) return

      this.isScanning = true
      this.error = null

      try {
        const response = await axios.post('/api/target', {
          domain: this.domain,
          rate_limit: this.rateLimit
        })

        // Redirigir a la página del target
        this.$router.push(`/target/${this.domain}/${response.data.scan_id}`)
      } catch (err) {
        this.error = err.response?.data?.error || 'Failed to create target'
        this.isScanning = false
      }
    },
    async loadRecentScans() {
      try {
        const response = await axios.get('/api/scans')
        this.recentScans = response.data.scans
      } catch (err) {
        console.error('Failed to load recent scans:', err)
      }
    },
    goToResults(scan) {
      // Siempre ir a la página de Target para ver las herramientas
      this.$router.push(`/target/${scan.domain}/${scan.id}`)
    },
    async deleteScan(scanId) {
      if (!confirm('Are you sure you want to delete this scan?')) return
      
      try {
        await axios.delete(`/api/scan/${scanId}`)
        // Recargar la lista de scans
        this.loadRecentScans()
      } catch (err) {
        console.error('Failed to delete scan:', err)
        alert('Failed to delete scan')
      }
    },
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleString()
    }
  }
}
</script>

<style scoped>
.home {
  min-height: 100vh;
  padding: 40px 20px;
}

.banner {
  text-align: center;
  margin-bottom: 50px;
}

.ascii-art {
  color: var(--accent-primary);
  font-size: 14px;
  line-height: 1.2;
  margin-bottom: 10px;
  font-family: monospace;
}

.subtitle {
  font-size: 20px;
  color: var(--text-secondary);
  margin-bottom: 5px;
}

.author {
  color: var(--text-secondary);
  font-size: 14px;
}

.scan-section {
  max-width: 600px;
  margin: 0 auto 40px;
}

.scan-section h2 {
  margin-bottom: 10px;
  color: var(--text-primary);
}

.description {
  color: var(--text-secondary);
  margin-bottom: 30px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-weight: 500;
}

.btn-scan {
  width: 100%;
  font-size: 18px;
  padding: 16px;
  margin-top: 10px;
}

.scanning-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
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

.error-message {
  margin-top: 15px;
  padding: 12px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid var(--danger);
  border-radius: 8px;
  color: var(--danger);
  text-align: center;
}

.recent-scans {
  max-width: 900px;
  margin: 0 auto;
}

.recent-scans h3 {
  margin-bottom: 20px;
}

.scans-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.scan-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 16px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.scan-item:hover {
  border-color: var(--accent-primary);
}

.scan-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.scan-content:hover {
  transform: translateX(5px);
}

.scan-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.scan-domain {
  font-weight: 600;
  font-size: 16px;
}

.scan-date {
  font-size: 12px;
  color: var(--text-secondary);
}

.scan-stats {
  display: flex;
  gap: 20px;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 12px;
  color: var(--text-secondary);
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent-primary);
}

.scan-status {
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.scan-status.completed {
  background: rgba(16, 185, 129, 0.2);
  color: var(--success);

.btn-delete {
  padding: 8px 12px;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  font-size: 18px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-delete:hover {
  background: var(--danger);
  border-color: var(--danger);
  transform: scale(1.1);
}
}

.scan-status.running {
  background: rgba(245, 158, 11, 0.2);
  color: var(--warning);
}

.scan-status.failed {
  background: rgba(239, 68, 68, 0.2);
  color: var(--danger);
}
</style>
