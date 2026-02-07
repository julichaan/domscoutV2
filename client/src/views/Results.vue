<template>
  <div class="results-view">
    <div class="container">
      <!-- Header -->
      <div class="result-header">
        <button class="btn btn-back" @click="goBack">
          ← Back
        </button>
        <div class="target-info">
          <h1>{{ scanInfo.domain }}</h1>
          <div class="meta">
            <span class="meta-item">
              <span class="label">Status:</span>
              <span class="status-badge" :class="scanInfo.status">{{ scanInfo.status }}</span>
            </span>
            <span class="meta-item">
              <span class="label">Duration:</span>
              <span>{{ formatDuration(scanInfo.duration) }}</span>
            </span>
            <span class="meta-item">
              <span class="label">Scan ID:</span>
              <span class="mono">{{ scanId.substring(0, 8) }}</span>
            </span>
          </div>
        </div>
      </div>

      <!-- Stats Bar -->
      <div class="stats-bar">
        <div class="stat-item">
          <span class="stat-value">{{ results.length }}</span>
          <span class="stat-label">Total Results</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.alive_urls }}</span>
          <span class="stat-label">Live URLs</span>
        </div>
        <div class="stat-item">
          <span class="stat-value">{{ stats.subdomains }}</span>
          <span class="stat-label">Subdomains</span>
        </div>
      </div>

      <!-- Search and Filters -->
      <div class="controls-bar">
        <input
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="Search by URL, status code, or title..."
        />
        <div class="filter-group">
          <button
            class="filter-btn"
            :class="{ active: statusFilter === null }"
            @click="statusFilter = null"
          >
            All
          </button>
          <button
            class="filter-btn"
            :class="{ active: statusFilter === 200 }"
            @click="statusFilter = 200"
          >
            200
          </button>
          <button
            class="filter-btn"
            :class="{ active: statusFilter === 300 }"
            @click="statusFilter = 300"
          >
            3xx
          </button>
          <button
            class="filter-btn"
            :class="{ active: statusFilter === 400 }"
            @click="statusFilter = 400"
          >
            4xx
          </button>
          <button
            class="filter-btn"
            :class="{ active: statusFilter === 500 }"
            @click="statusFilter = 500"
          >
            5xx
          </button>
        </div>
      </div>

      <!-- Results Table -->
      <div v-if="filteredResults.length > 0" class="results-table-container">
        <table class="results-table">
          <thead>
            <tr>
              <th class="col-screenshot">Screenshot</th>
              <th class="col-status">Status</th>
              <th class="col-url">URL</th>
              <th class="col-title">Title</th>
              <th class="col-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(result, index) in filteredResults"
              :key="index"
              class="result-row"
            >
              <td class="col-screenshot">
                <div
                  v-if="result.screenshot"
                  class="screenshot-thumbnail"
                  @click="openScreenshotModal(result)"
                >
                  <img
                    :src="'/screenshots/' + result.screenshot.filename"
                    :alt="result.url"
                    @error="handleImageError"
                  />
                  <div class="thumbnail-overlay">
                    <span class="zoom-icon">🔍</span>
                  </div>
                </div>
                <div v-else class="no-screenshot">
                  <span>No Screenshot</span>
                </div>
              </td>
              <td class="col-status">
                <span
                  class="status-code"
                  :class="'status-' + Math.floor((result.status_code || 0) / 100)"
                >
                  {{ result.status_code || '---' }}
                </span>
              </td>
              <td class="col-url">
                <a
                  :href="result.url"
                  target="_blank"
                  class="url-link"
                  :title="result.url"
                >
                  {{ result.url }}
                </a>
              </td>
              <td class="col-title">
                <span class="page-title" :title="result.title">
                  {{ result.title || '-' }}
                </span>
              </td>
              <td class="col-actions">
                <button
                  class="btn-action"
                  @click="copyToClipboard(result.url)"
                  title="Copy URL"
                >
                  📋
                </button>
                <button
                  v-if="result.screenshot"
                  class="btn-action"
                  @click="openScreenshotModal(result)"
                  title="View Screenshot"
                >
                  🖼️
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- No Results Message -->
      <div v-else class="no-data">
        <div class="icon">🔍</div>
        <h3>No Results Found</h3>
        <p v-if="searchQuery">Try adjusting your search query.</p>
        <p v-else>The scan hasn't produced any results yet.</p>
      </div>

      <!-- Expandable Sections for Raw Data -->
      <div class="expandable-sections">
        <!-- Subdomains Section -->
        <div class="section-card">
          <div class="section-title" @click="toggleSection('subdomains')">
            <h3>🌐 All Subdomains ({{ subdomains.length }})</h3>
            <span class="toggle-icon">{{ expandedSections.subdomains ? '▼' : '▶' }}</span>
          </div>
          <div v-if="expandedSections.subdomains" class="section-content">
            <input
              v-model="subdomainSearch"
              type="text"
              class="search-input"
              placeholder="Search subdomains..."
            />
            <div class="subdomain-list">
              <div
                v-for="subdomain in filteredSubdomains"
                :key="subdomain"
                class="subdomain-item"
              >
                {{ subdomain }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Screenshot Modal -->
    <div v-if="selectedResult" class="modal-overlay" @click="closeModal">
      <div class="modal-container" @click.stop>
        <button class="modal-close-btn" @click="closeModal">✕</button>
        <div class="modal-body">
          <div class="modal-image-container">
            <img
              v-if="selectedResult.screenshot"
              :src="'/screenshots/' + selectedResult.screenshot.filename"
              :alt="selectedResult.url"
            />
          </div>
          <div class="modal-details">
            <div class="modal-url">
              <span
                class="status-code large"
                :class="'status-' + Math.floor((selectedResult.status_code || 0) / 100)"
              >
                {{ selectedResult.status_code || '---' }}
              </span>
              <a :href="selectedResult.url" target="_blank" class="url-link">
                {{ selectedResult.url }}
              </a>
            </div>
            <div v-if="selectedResult.title" class="modal-title">
              <strong>Title:</strong> {{ selectedResult.title }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Results',
  data() {
    return {
      scanId: '',
      scanInfo: {
        domain: '',
        status: 'running',
        duration: 0
      },
      stats: {
        subdomains: 0,
        alive_urls: 0,
        screenshots: 0
      },
      screenshots: [],
      urls: [],
      subdomains: [],
      results: [],  // Combined results for table view
      searchQuery: '',
      subdomainSearch: '',
      statusFilter: null,
      selectedResult: null,
      expandedSections: {
        subdomains: false
      },
      pollInterval: null
    }
  },
  computed: {
    filteredResults() {
      let filtered = this.results

      // Apply search filter
      if (this.searchQuery) {
        const search = this.searchQuery.toLowerCase()
        filtered = filtered.filter(r =>
          r.url.toLowerCase().includes(search) ||
          (r.title && r.title.toLowerCase().includes(search)) ||
          (r.status_code && r.status_code.toString().includes(search))
        )
      }

      // Apply status code filter
      if (this.statusFilter !== null) {
        if (this.statusFilter === 200) {
          filtered = filtered.filter(r => r.status_code >= 200 && r.status_code < 300)
        } else if (this.statusFilter === 300) {
          filtered = filtered.filter(r => r.status_code >= 300 && r.status_code < 400)
        } else if (this.statusFilter === 400) {
          filtered = filtered.filter(r => r.status_code >= 400 && r.status_code < 500)
        } else if (this.statusFilter === 500) {
          filtered = filtered.filter(r => r.status_code >= 500)
        }
      }

      return filtered
    },
    filteredSubdomains() {
      if (!this.subdomainSearch) return this.subdomains
      const search = this.subdomainSearch.toLowerCase()
      return this.subdomains.filter(s => s.toLowerCase().includes(search))
    }
  },
  mounted() {
    this.scanId = this.$route.params.scanId
    this.loadScanInfo()
    this.startPolling()
  },
  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval)
    }
  },
  methods: {
    async loadScanInfo() {
      try {
        const response = await axios.get(`/api/scan/${this.scanId}`)
        this.scanInfo = response.data.scan
        this.stats = response.data.stats

        if (this.scanInfo.status === 'completed') {
          await this.loadResults()
          if (this.pollInterval) {
            clearInterval(this.pollInterval)
          }
        }
      } catch (err) {
        console.error('Failed to load scan info:', err)
      }
    },
    async loadResults() {
      try {
        const [screenshotsRes, urlsRes, subdomainsRes] = await Promise.all([
          axios.get(`/api/scan/${this.scanId}/screenshots`),
          axios.get(`/api/scan/${this.scanId}/urls`),
          axios.get(`/api/scan/${this.scanId}/subdomains`)
        ])

        this.screenshots = screenshotsRes.data.screenshots
        this.urls = urlsRes.data.urls
        this.subdomains = subdomainsRes.data.subdomains

        // Combine URLs and screenshots into unified results
        this.buildResultsList()
      } catch (err) {
        console.error('Failed to load results:', err)
      }
    },
    buildResultsList() {
      // Create a map of screenshots by URL
      const screenshotMap = {}
      this.screenshots.forEach(ss => {
        screenshotMap[ss.url] = ss
      })

      // Build results by merging URLs with their screenshots
      this.results = this.urls.map(urlData => {
        const screenshot = screenshotMap[urlData.url]
        return {
          url: urlData.url,
          status_code: urlData.status_code,
          title: screenshot ? screenshot.title : (urlData.title || null),
          screenshot: screenshot || null
        }
      })

      // Sort by status code (successful first)
      this.results.sort((a, b) => {
        const codeA = a.status_code || 999
        const codeB = b.status_code || 999
        return codeA - codeB
      })
    },
    startPolling() {
      this.pollInterval = setInterval(() => {
        if (this.scanInfo.status === 'running') {
          this.loadScanInfo()
        }
      }, 3000)
    },
    toggleSection(section) {
      this.expandedSections[section] = !this.expandedSections[section]
    },
    goBack() {
      this.$router.push('/')
    },
    openScreenshotModal(result) {
      this.selectedResult = result
    },
    closeModal() {
      this.selectedResult = null
    },
    copyToClipboard(text) {
      navigator.clipboard.writeText(text).then(() => {
        // Could add a toast notification here
        console.log('Copied to clipboard:', text)
      }).catch(err => {
        console.error('Failed to copy:', err)
      })
    },
    handleImageError(e) {
      e.target.src = 'data:image/svg+xml,%3Csvg width="400" height="300" xmlns="http://www.w3.org/2000/svg"%3E%3Crect width="400" height="300" fill="%23222"/%3E%3Ctext x="50%25" y="50%25" font-family="Arial" font-size="18" fill="%23999" text-anchor="middle"%3EImage not found%3C/text%3E%3C/svg%3E'
    },
    formatDuration(seconds) {
      if (!seconds) return '0s'
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
    }
  }
}
</script>

<style scoped>
.results-view {
  min-height: 100vh;
  padding: 20px;
  background: var(--bg-primary);
}

.container {
  max-width: 1600px;
  margin: 0 auto;
}

/* Header */
.result-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
  padding: 24px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
}

.btn-back {
  padding: 10px 20px;
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.btn-back:hover {
  background: var(--bg-primary);
  border-color: var(--accent-primary);
}

.target-info {
  flex: 1;
}

.target-info h1 {
  font-size: 28px;
  color: var(--accent-primary);
  margin-bottom: 10px;
  word-break: break-all;
}

.meta {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.label {
  color: var(--text-secondary);
}

.mono {
  font-family: monospace;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.running {
  background: #fbbf2415;
  color: #fbbf24;
}

.status-badge.completed {
  background: #10b98115;
  color: #10b981;
}

.status-badge.failed {
  background: #ef444415;
  color: #ef4444;
}

/* Stats Bar */
.stats-bar {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-item {
  padding: 20px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 32px;
  font-weight: 700;
  color: var(--accent-primary);
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
}

/* Controls Bar */
.controls-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  align-items: center;
}

.search-input {
  flex: 1;
  min-width: 300px;
  padding: 12px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  border-radius: 6px;
  font-size: 14px;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent-primary);
}

.filter-group {
  display: flex;
  gap: 8px;
}

.filter-btn {
  padding: 8px 16px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 13px;
  font-weight: 500;
}

.filter-btn:hover {
  border-color: var(--accent-primary);
  color: var(--text-primary);
}

.filter-btn.active {
  background: var(--accent-primary);
  border-color: var(--accent-primary);
  color: #000;
}

/* Results Table */
.results-table-container {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 30px;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
}

.results-table thead {
  background: var(--bg-tertiary);
  border-bottom: 2px solid var(--border-color);
}

.results-table th {
  padding: 16px;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.results-table tbody tr {
  border-bottom: 1px solid var(--border-color);
  transition: background 0.2s;
}

.results-table tbody tr:hover {
  background: var(--bg-tertiary);
}

.results-table tbody tr:last-child {
  border-bottom: none;
}

.results-table td {
  padding: 16px;
  vertical-align: middle;
}

/* Table Columns */
.col-screenshot {
  width: 180px;
}

.col-status {
  width: 100px;
}

.col-url {
  min-width: 300px;
  max-width: 500px;
}

.col-title {
  min-width: 200px;
}

.col-actions {
  width: 120px;
  text-align: center;
}

/* Screenshot Thumbnail */
.screenshot-thumbnail {
  position: relative;
  width: 150px;
  height: 100px;
  border-radius: 6px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid var(--border-color);
}

.screenshot-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.screenshot-thumbnail:hover .thumbnail-overlay {
  opacity: 1;
}

.zoom-icon {
  font-size: 32px;
}

.no-screenshot {
  width: 150px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border: 1px dashed var(--border-color);
  border-radius: 6px;
  color: var(--text-secondary);
  font-size: 12px;
}

/* Status Code */
.status-code {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
  font-family: monospace;
}

.status-code.status-2 {
  background: #10b98115;
  color: #10b981;
}

.status-code.status-3 {
  background: #3b82f615;
  color: #3b82f6;
}

.status-code.status-4 {
  background: #f59e0b15;
  color: #f59e0b;
}

.status-code.status-5 {
  background: #ef444415;
  color: #ef4444;
}

.status-code.status-0 {
  background: #6b728015;
  color: #6b7280;
}

/* URL Link */
.url-link {
  color: var(--accent-primary);
  text-decoration: none;
  font-size: 13px;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.url-link:hover {
  text-decoration: underline;
}

/* Page Title */
.page-title {
  font-size: 13px;
  color: var(--text-secondary);
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Action Buttons */
.btn-action {
  padding: 8px 12px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
  margin: 0 4px;
}

.btn-action:hover {
  background: var(--bg-primary);
  border-color: var(--accent-primary);
  transform: scale(1.1);
}

/* No Results */
.no-data {
  text-align: center;
  padding: 80px 20px;
  color: var(--text-secondary);
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  margin-bottom: 30px;
}

.no-data .icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.no-data h3 {
  font-size: 24px;
  margin-bottom: 8px;
  color: var(--text-primary);
}

/* Expandable Sections */
.expandable-sections {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.section-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.section-title:hover {
  background: var(--bg-tertiary);
}

.section-title h3 {
  font-size: 18px;
  color: var(--text-primary);
}

.toggle-icon {
  color: var(--accent-primary);
  font-size: 14px;
}

.section-content {
  padding: 0 20px 20px 20px;
  border-top: 1px solid var(--border-color);
}

.section-content .search-input {
  width: 100%;
  margin: 15px 0;
}

.subdomain-list {
  max-height: 400px;
  overflow-y: auto;
}

.subdomain-item {
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
  font-family: monospace;
  font-size: 13px;
  color: var(--text-primary);
}

.subdomain-item:last-child {
  border-bottom: none;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  animation: fadeIn 0.2s;
}

.modal-container {
  max-width: 1200px;
  width: 100%;
  max-height: 90vh;
  background: var(--bg-secondary);
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-close-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  border: none;
  color: var(--text-primary);
  font-size: 20px;
  cursor: pointer;
  z-index: 10;
  transition: all 0.2s;
}

.modal-close-btn:hover {
  background: var(--accent-primary);
  color: #000;
}

.modal-body {
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.modal-image-container {
  background: #000;
  text-align: center;
  padding: 20px;
}

.modal-image-container img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}

.modal-details {
  padding: 24px;
}

.modal-url {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.status-code.large {
  font-size: 16px;
  padding: 8px 16px;
}

.modal-title {
  font-size: 14px;
  color: var(--text-secondary);
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@media (max-width: 1200px) {
  .col-screenshot {
    width: 150px;
  }
  
  .screenshot-thumbnail {
    width: 120px;
    height: 80px;
  }

  .no-screenshot {
    width: 120px;
    height: 80px;
  }
}

@media (max-width: 768px) {
  .results-table-container {
    overflow-x: auto;
  }

  .results-table {
    min-width: 900px;
  }

  .controls-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input {
    min-width: 100%;
  }

  .filter-group {
    width: 100%;
    overflow-x: auto;
  }

  .result-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
