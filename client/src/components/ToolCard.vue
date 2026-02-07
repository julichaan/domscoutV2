<template>
  <div class="tool-card card" :class="{ disabled: disabled }">
    <div class="tool-header">
      <div class="tool-info">
        <h3>{{ title }}</h3>
        <p>{{ description }}</p>
      </div>
    </div>

    <div class="tool-status">
      <div v-if="status === 'idle'" class="status-badge status-idle">
        ⏸️ Not Started
      </div>
      <div v-else-if="status === 'running'" class="status-badge status-running">
        <span class="spinner-tiny"></span> Running...
      </div>
      <div v-else-if="status === 'completed'" class="status-badge status-completed">
        ✅ Completed
      </div>
      <div v-else-if="status === 'failed'" class="status-badge status-failed">
        ❌ Failed
      </div>

      <div v-if="count > 0" class="tool-count">
        <span class="count-value">{{ count }}</span>
        <span class="count-label">results</span>
      </div>
    </div>

    <div class="tool-actions">
      <button 
        class="btn btn-primary btn-run"
        @click="$emit('run')"
        :disabled="disabled || status === 'running'"
      >
        <span v-if="status === 'running'">Running...</span>
        <span v-else-if="status === 'completed'">🔄 Re-run</span>
        <span v-else>▶️ Run Tool</span>
      </button>
      
      <button
        v-if="status === 'completed' && count > 0"
        class="btn btn-secondary btn-results"
        @click="$emit('view-results')"
      >
        📋 Results
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ToolCard',
  props: {
    title: {
      type: String,
      required: true
    },
    description: {
      type: String,
      required: true
    },
    status: {
      type: String,
      default: 'idle', // idle, running, completed, failed
      validator: (value) => ['idle', 'running', 'completed', 'failed'].includes(value)
    },
    count: {
      type: Number,
      default: 0
    },
    disabled: {
      type: Boolean,
      default: false
    }
  },
  emits: ['run', 'view-results']
}
</script>

<style scoped>
.tool-card {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.tool-card:not(.disabled):hover {
  border-color: var(--accent-primary);
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0, 217, 255, 0.15);
}

.tool-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tool-header {
  display: flex;
  gap: 15px;
  align-items: flex-start;
}

.tool-info {
  flex: 1;
  width: 100%;
}

.tool-info h3 {
  font-size: 20px;
  margin: 0 0 8px 0;
  color: var(--text-primary);
}

.tool-info p {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

.tool-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 600;
}

.status-idle {
  background: rgba(160, 174, 192, 0.15);
  color: var(--text-secondary);
}

.status-running {
  background: rgba(245, 158, 11, 0.15);
  color: var(--warning);
}

.status-completed {
  background: rgba(16, 185, 129, 0.15);
  color: var(--success);
}

.status-failed {
  background: rgba(239, 68, 68, 0.15);
  color: var(--danger);
}

.tool-count {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 6px 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
}

.count-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--accent-primary);
  line-height: 1;
}

.count-label {
  font-size: 11px;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tool-actions {
  display: flex;
  gap: 10px;
}

.btn-run {
  flex: 1;
  padding: 12px;
  font-size: 15px;
  font-weight: 600;
}

.btn-run:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-results {
  padding: 12px 20px;
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
}

.spinner-tiny {
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Running animation effect */
.tool-card:has(.status-running)::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(0, 217, 255, 0.1),
    transparent
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  to {
    left: 100%;
  }
}
</style>
