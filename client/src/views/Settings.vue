<template>
  <div class="settings-view">
    <div class="container">
      <!-- Header -->
      <div class="settings-header card">
        <button class="btn btn-secondary btn-back" @click="goBack">
          ← Back
        </button>
        <div class="header-info">
          <h1>⚙️ Settings</h1>
          <p>Configure DomScout preferences</p>
        </div>
      </div>

      <!-- Settings Sections -->
      <div class="settings-sections">
        <!-- User Agent Rotation -->
        <div class="setting-card card">
          <div class="setting-header">
            <div class="setting-info">
              <h3>🔄 User-Agent Rotation</h3>
              <p>Rotate through legitimate user agents to avoid detection</p>
            </div>
            <label class="toggle-switch">
              <input 
                type="checkbox" 
                v-model="rotateUserAgents"
                @change="saveUserAgentSetting"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
          <div class="setting-description">
            When enabled, scanning tools (HTTPx, GAU, GoSpider, GoWitness) will use a random user agent from a pool of 50 legitimate browser signatures. This helps avoid rate limiting and detection by web application firewalls.
          </div>
          <div v-if="userAgentMessage" :class="['setting-message', userAgentMessageType]">
            {{ userAgentMessage }}
          </div>
        </div>

        <!-- Subfinder Configuration -->
        <div class="setting-card card">
          <div class="setting-header">
            <div class="setting-info">
              <h3>🔑 Subfinder API Keys</h3>
              <p>Configure API keys for subdomain enumeration sources</p>
            </div>
            <button 
              class="btn btn-primary"
              @click="openSubfinderEditor"
            >
              Edit Configuration
            </button>
          </div>
          <div class="setting-description">
            Add your API keys for services like Shodan, Censys, VirusTotal, etc. to enhance Subfinder's subdomain discovery capabilities. The configuration file is located at: <code>~/.config/subfinder/provider-config.yaml</code>
          </div>
        </div>
      </div>

      <!-- Subfinder Config Modal -->
      <div v-if="showSubfinderModal" class="modal" @click="closeSubfinderModal">
        <div class="modal-content modal-large" @click.stop>
          <button class="modal-close" @click="closeSubfinderModal">×</button>
          <h3>📝 Subfinder Provider Configuration</h3>
          <p class="modal-subtitle">
            Add your API keys below. Visit 
            <a href="https://github.com/projectdiscovery/subfinder" target="_blank">Subfinder Documentation</a>
            for more information.
          </p>
          
          <div class="config-path">
            <strong>File:</strong> <code>{{ subfinderConfigPath }}</code>
          </div>

          <div class="editor-container">
            <textarea
              v-model="subfinderConfig"
              class="config-editor"
              placeholder="# Example:
# shodan:
#   - your-api-key-here
# censys:
#   - your-api-id:your-api-secret
# virustotal:
#   - your-api-key-here"
              spellcheck="false"
            ></textarea>
          </div>

          <div v-if="subfinderMessage" :class="['modal-message', subfinderMessageType]">
            {{ subfinderMessage }}
          </div>

          <div class="modal-actions">
            <button class="btn btn-secondary" @click="closeSubfinderModal">
              Cancel
            </button>
            <button 
              class="btn btn-primary"
              @click="saveSubfinderConfig"
              :disabled="savingSubfinder"
            >
              <span v-if="!savingSubfinder">💾 Save Configuration</span>
              <span v-else>
                <span class="spinner-small"></span> Saving...
              </span>
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
  name: 'SettingsView',
  data() {
    return {
      // User Agent Rotation
      rotateUserAgents: false,
      userAgentMessage: '',
      userAgentMessageType: 'success',
      
      // Subfinder Config
      showSubfinderModal: false,
      subfinderConfig: '',
      subfinderConfigPath: '',
      subfinderMessage: '',
      subfinderMessageType: 'success',
      savingSubfinder: false
    }
  },
  mounted() {
    this.loadSettings()
  },
  methods: {
    async loadSettings() {
      try {
        const response = await axios.get('/api/settings')
        this.rotateUserAgents = response.data.settings.rotate_user_agents || false
      } catch (err) {
        console.error('Failed to load settings:', err)
      }
    },
    
    async saveUserAgentSetting() {
      try {
        const response = await axios.post('/api/settings/user-agents', {
          enabled: this.rotateUserAgents
        })
        
        if (response.data.success) {
          this.userAgentMessage = 'User-Agent rotation preference saved!'
          this.userAgentMessageType = 'success'
        } else {
          this.userAgentMessage = 'Failed to save setting: ' + response.data.error
          this.userAgentMessageType = 'error'
        }
        
        // Clear message after 3 seconds
        setTimeout(() => {
          this.userAgentMessage = ''
        }, 3000)
      } catch (err) {
        console.error('Failed to save user agent setting:', err)
        this.userAgentMessage = 'Error: ' + err.message
        this.userAgentMessageType = 'error'
      }
    },
    
    async openSubfinderEditor() {
      this.showSubfinderModal = true
      this.subfinderMessage = ''
      
      try {
        const response = await axios.get('/api/settings/subfinder-config')
        if (response.data.success) {
          this.subfinderConfig = response.data.content
          this.subfinderConfigPath = response.data.path
        } else {
          this.subfinderMessage = 'Error loading config: ' + response.data.error
          this.subfinderMessageType = 'error'
        }
      } catch (err) {
        console.error('Failed to load subfinder config:', err)
        this.subfinderMessage = 'Error: ' + err.message
        this.subfinderMessageType = 'error'
      }
    },
    
    closeSubfinderModal() {
      this.showSubfinderModal = false
      this.subfinderMessage = ''
      this.savingSubfinder = false
    },
    
    async saveSubfinderConfig() {
      this.savingSubfinder = true
      this.subfinderMessage = ''
      
      try {
        const response = await axios.post('/api/settings/subfinder-config', {
          content: this.subfinderConfig
        })
        
        if (response.data.success) {
          this.subfinderMessage = 'Configuration saved successfully!'
          this.subfinderMessageType = 'success'
          
          // Close modal after 1.5 seconds
          setTimeout(() => {
            this.closeSubfinderModal()
          }, 1500)
        } else {
          this.subfinderMessage = 'Failed to save: ' + response.data.error
          this.subfinderMessageType = 'error'
        }
      } catch (err) {
        console.error('Failed to save subfinder config:', err)
        this.subfinderMessage = 'Error: ' + err.message
        this.subfinderMessageType = 'error'
      } finally {
        this.savingSubfinder = false
      }
    },
    
    goBack() {
      this.$router.push('/')
    }
  }
}
</script>

<style scoped>
.settings-view {
  min-height: 100vh;
  padding: 40px 20px;
}

.settings-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 40px;
  padding: 30px;
}

.btn-back {
  white-space: nowrap;
}

.header-info {
  flex: 1;
}

.header-info h1 {
  font-size: 32px;
  margin: 0 0 8px 0;
  color: var(--accent-primary);
}

.header-info p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 16px;
}

.settings-sections {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.setting-card {
  padding: 32px;
}

.setting-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 20px;
}

.setting-info h3 {
  font-size: 22px;
  margin: 0 0 8px 0;
  color: var(--text-primary);
}

.setting-info p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.setting-description {
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 14px;
  margin-top: 12px;
}

.setting-description code {
  background: var(--bg-tertiary);
  padding: 2px 8px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 13px;
  color: var(--accent-primary);
}

/* Toggle Switch */
.toggle-switch {
  position: relative;
  display: inline-block;
  width: 60px;
  height: 34px;
  flex-shrink: 0;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--bg-tertiary);
  transition: 0.3s;
  border-radius: 34px;
  border: 2px solid var(--border-color);
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 22px;
  width: 22px;
  left: 4px;
  bottom: 4px;
  background-color: var(--text-secondary);
  transition: 0.3s;
  border-radius: 50%;
}

input:checked + .toggle-slider {
  background-color: var(--accent-primary);
  border-color: var(--accent-primary);
}

input:checked + .toggle-slider:before {
  transform: translateX(26px);
  background-color: white;
}

input:focus + .toggle-slider {
  box-shadow: 0 0 0 3px rgba(30, 215, 96, 0.3);
}

/* Messages */
.setting-message {
  margin-top: 16px;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  animation: fadeIn 0.3s ease;
}

.setting-message.success {
  background: rgba(30, 215, 96, 0.15);
  color: var(--accent-primary);
  border: 1px solid var(--accent-primary);
}

.setting-message.error {
  background: rgba(255, 50, 50, 0.15);
  color: #ff5252;
  border: 1px solid #ff5252;
}

/* Modal */
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

.modal-large {
  max-width: 900px;
  max-height: 90vh;
}

.modal-content {
  width: 100%;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 32px;
  position: relative;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
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
  z-index: 1;
}

.modal-close:hover {
  background: var(--accent-primary);
  color: white;
}

.modal-content h3 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: var(--accent-primary);
  padding-right: 50px;
}

.modal-subtitle {
  color: var(--text-secondary);
  margin: 0 0 20px 0;
  line-height: 1.5;
}

.modal-subtitle a {
  color: var(--accent-primary);
  text-decoration: none;
}

.modal-subtitle a:hover {
  text-decoration: underline;
}

.config-path {
  background: var(--bg-tertiary);
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 14px;
  color: var(--text-secondary);
}

.config-path code {
  color: var(--accent-primary);
  font-family: 'Courier New', monospace;
}

.editor-container {
  flex: 1;
  margin-bottom: 20px;
}

.config-editor {
  width: 100%;
  min-height: 400px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 16px;
  color: var(--text-primary);
  font-family: 'Courier New', 'Monaco', monospace;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  transition: all 0.3s ease;
}

.config-editor:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(30, 215, 96, 0.2);
}

.modal-message {
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease;
}

.modal-message.success {
  background: rgba(30, 215, 96, 0.15);
  color: var(--accent-primary);
  border: 1px solid var(--accent-primary);
}

.modal-message.error {
  background: rgba(255, 50, 50, 0.15);
  color: #ff5252;
  border: 1px solid #ff5252;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.modal-actions .btn {
  min-width: 140px;
}

.spinner-small {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  display: inline-block;
  animation: spin 1s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .settings-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .setting-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .toggle-switch {
    align-self: flex-start;
  }
  
  .modal-actions {
    flex-direction: column;
  }
  
  .modal-actions .btn {
    width: 100%;
  }
}
</style>
