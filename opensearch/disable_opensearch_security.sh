#!/bin/bash -x

# Define OpenSearch version and installation directory
OPENSEARCH_VER="2.12.0"
INSTALL_DIR="/home/cdsw/opensearch-app"
CONFIG_FILE="${INSTALL_DIR}/opensearch-${OPENSEARCH_VER}/config/opensearch.yml"

# Backup the original opensearch.yml file
cp $CONFIG_FILE ${CONFIG_FILE}.bak

# Disable security plugin by adding the required setting
echo "Disabling OpenSearch security plugin..."
echo "plugins.security.disabled: true" >> $CONFIG_FILE
