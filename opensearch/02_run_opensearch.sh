#!/bin/bash -x

# Define OpenSearch version and installation directory
OPENSEARCH_VER="2.12.0"
INSTALL_DIR="/home/cdsw/opensearch-app"
OPENSEARCH_DIR="${INSTALL_DIR}/opensearch-${OPENSEARCH_VER}"
CONFIG_FILE="${OPENSEARCH_DIR}/config/opensearch.yml"
LOG_FILE="${OPENSEARCH_DIR}/logs/opensearch.log"
PID_FILE="${OPENSEARCH_DIR}/opensearch.pid"

# Define default port (override with argument or environment variable)
#OPENSEARCH_PORT=${1:-${CDSW_READONLY_PORT:-9200}}
OPENSEARCH_PORT=9200

# Ensure required environment variables are set
if [[ -z "$CDSW_ENGINE_ID" ]]; then
  echo "❌ ERROR: Environment variable CDSW_ENGINE_ID is not set!"
  exit 1
fi

# Set JAVA_HOME
# export JAVA_VER="11.0.1"
# export JAVA_HOME="/home/cdsw/solr-app/jdk-${JAVA_VER}"
export JAVA_HOME="/home/cdsw/opensearch-app/opensearch-2.12.0/jdk"
echo "Using JAVA: $(${JAVA_HOME}/bin/java -version)"

# Kill any existing OpenSearch process if running
if [[ -f "$PID_FILE" ]]; then
  PID=$(cat "$PID_FILE")
  if ps -p $PID > /dev/null 2>&1; then
    echo "Stopping existing OpenSearch process ($PID)..."
    kill $PID
    sleep 5
  fi
  rm -f "$PID_FILE"
fi

# Dynamically update OpenSearch configuration
echo "🔧 Updating OpenSearch configuration..."
cat <<EOF > "$CONFIG_FILE"
# OpenSearch Configuration

# Cluster settings
cluster.name: opensearch-cluster
node.name: "$CDSW_ENGINE_ID"

# Network settings
network.host: 127.0.0.1
#network.host: $CDSW_IP_ADDRESS
#http.port: $CDSW_APP_PORT
http.port: $CDSW_APP_PORT
transport.port: $OPENSEARCH_PORT

# Discovery settings (required for non-loopback address)
#discovery.seed_hosts: [$CDSW_IP_ADDRESS]
#cluster.initial_cluster_manager_nodes: ["$CDSW_ENGINE_ID"]

# Disable security plugin for simplicity
plugins.security.disabled: true
EOF

echo "✅ Configuration updated."

# Start OpenSearch using nohup so it stays running
echo "🚀 Starting OpenSearch on port $OPENSEARCH_PORT..."
cd "$OPENSEARCH_DIR"
nohup bin/opensearch > "$LOG_FILE" 2>&1 & echo $! > "$PID_FILE"

# Allow some time for OpenSearch to start
sleep 10

# Verify if OpenSearch started successfully
if ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
  echo "✅ OpenSearch is running on port $OPENSEARCH_PORT."
else
  echo "❌ Failed to start OpenSearch. Check logs at $LOG_FILE."
  exit 1
fi
