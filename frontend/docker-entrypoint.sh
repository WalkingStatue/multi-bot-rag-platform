#!/bin/sh

# Docker entrypoint script for frontend
set -e

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log "Starting frontend container..."

# Create runtime configuration file from environment variables
cat > /usr/share/nginx/html/config.js << EOF
window.ENV = {
  VITE_API_URL: '${VITE_API_URL:-http://localhost:8000}',
  VITE_WS_URL: '${VITE_WS_URL:-ws://localhost:8000/ws}',
  VITE_API_TIMEOUT: '${VITE_API_TIMEOUT:-30000}',
  VITE_WS_RECONNECT_INTERVAL: '${VITE_WS_RECONNECT_INTERVAL:-5000}',
  VITE_WS_MAX_RECONNECT_ATTEMPTS: '${VITE_WS_MAX_RECONNECT_ATTEMPTS:-10}',
  VITE_AUTH_TOKEN_KEY: '${VITE_AUTH_TOKEN_KEY:-auth_token}',
  VITE_AUTH_REFRESH_TOKEN_KEY: '${VITE_AUTH_REFRESH_TOKEN_KEY:-refresh_token}',
  VITE_AUTH_TOKEN_EXPIRY_BUFFER: '${VITE_AUTH_TOKEN_EXPIRY_BUFFER:-300000}',
  VITE_ENABLE_OFFLINE_MODE: '${VITE_ENABLE_OFFLINE_MODE:-true}',
  VITE_ENABLE_PERFORMANCE_MONITORING: '${VITE_ENABLE_PERFORMANCE_MONITORING:-true}',
  VITE_ENABLE_ERROR_REPORTING: '${VITE_ENABLE_ERROR_REPORTING:-true}',
  VITE_ENABLE_ANALYTICS: '${VITE_ENABLE_ANALYTICS:-false}',
  VITE_LOG_LEVEL: '${VITE_LOG_LEVEL:-info}',
  VITE_ENABLE_REMOTE_LOGGING: '${VITE_ENABLE_REMOTE_LOGGING:-false}',
  VITE_LOG_ENDPOINT: '${VITE_LOG_ENDPOINT:-}',
  VITE_MEMORY_TRACKING_INTERVAL: '${VITE_MEMORY_TRACKING_INTERVAL:-30000}',
  VITE_ENABLE_PERFORMANCE_WARNINGS: '${VITE_ENABLE_PERFORMANCE_WARNINGS:-true}',
  VITE_PWA_ENABLED: '${VITE_PWA_ENABLED:-true}',
  VITE_PWA_CACHE_NAME: '${VITE_PWA_CACHE_NAME:-rag-platform-cache}',
  VITE_ENABLE_MOCK_API: '${VITE_ENABLE_MOCK_API:-false}',
  VITE_ENABLE_DEBUG_MODE: '${VITE_ENABLE_DEBUG_MODE:-false}',
  VITE_SHOW_PERFORMANCE_METRICS: '${VITE_SHOW_PERFORMANCE_METRICS:-false}',
  VITE_SENTRY_DSN: '${VITE_SENTRY_DSN:-}',
  VITE_GOOGLE_ANALYTICS_ID: '${VITE_GOOGLE_ANALYTICS_ID:-}',
  VITE_HOTJAR_ID: '${VITE_HOTJAR_ID:-}',
  VITE_CSP_NONCE: '${VITE_CSP_NONCE:-}',
  VITE_ENABLE_HTTPS: '${VITE_ENABLE_HTTPS:-false}'
};
EOF

log "Runtime configuration created"

# Update index.html to include runtime config
if [ -f /usr/share/nginx/html/index.html ]; then
    # Add config script to head section
    sed -i 's|</head>|  <script src="/config.js"></script>\n  </head>|' /usr/share/nginx/html/index.html
    log "Updated index.html with runtime configuration"
fi

# Create health check endpoint
cat > /usr/share/nginx/html/health << EOF
healthy
EOF

log "Health check endpoint created"

# Validate nginx configuration
nginx -t

if [ $? -eq 0 ]; then
    log "Nginx configuration is valid"
else
    log "ERROR: Nginx configuration is invalid"
    exit 1
fi

# Set proper permissions
chown -R nginx:nginx /usr/share/nginx/html
chmod -R 755 /usr/share/nginx/html

log "Permissions set correctly"

# Print environment info
log "Environment: ${NODE_ENV:-production}"
log "API URL: ${VITE_API_URL:-http://localhost:8000}"
log "WebSocket URL: ${VITE_WS_URL:-ws://localhost:8000/ws}"

# Execute the main command
log "Starting nginx..."
exec "$@"