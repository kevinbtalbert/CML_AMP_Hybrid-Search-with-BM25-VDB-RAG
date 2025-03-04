#!/bin/bash -x

# Define OpenSearch version and configuration file
OPENSEARCH_VER="2.12.0"
INSTALL_DIR="/home/cdsw/opensearch-app"
CONFIG_FILE="${INSTALL_DIR}/opensearch-${OPENSEARCH_VER}/config/opensearch.yml"

# Define desired network settings
NEW_HOST="0.0.0.0"
NEW_PORT="8090"

# Backup the original opensearch.yml file
cp $CONFIG_FILE ${CONFIG_FILE}.bak

# Update the OpenSearch configuration file
echo "Updating OpenSearch configuration to use network host: $NEW_HOST and port: $NEW_PORT..."

# Use sed to modify or add the settings
sed -i "/^network.host:/d" $CONFIG_FILE
sed -i "/^http.port:/d" $CONFIG_FILE

# Append new settings
echo "network.host: $NEW_HOST" >> $CONFIG_FILE
echo "http.port: $NEW_PORT" >> $CONFIG_FILE

# Restart OpenSearch
echo "Restarting OpenSearch..."
# sh ${INSTALL_DIR}/opensearch-${OPENSEARCH_VER}/bin/opensearch-stop.sh || true  # Stop if running
nohup sh ${INSTALL_DIR}/opensearch-${OPENSEARCH_VER}/bin/opensearch > ${INSTALL_DIR}/opensearch.log 2>&1 &

# Wait for OpenSearch to start
sleep 10

# Verify OpenSearch is running
if curl -s "http://localhost:$NEW_PORT" | grep -q "opensearch"; then
  echo "OpenSearch is running on port $NEW_PORT."
else
  echo "Failed to start OpenSearch on port $NEW_PORT. Check logs at ${INSTALL_DIR}/opensearch.log."
fi
