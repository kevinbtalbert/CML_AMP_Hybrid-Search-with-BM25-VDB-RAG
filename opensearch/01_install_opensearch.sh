#!/bin/bash -x

# Define OpenSearch version and installation directory
OPENSEARCH_VER="2.12.0"  # Adjust to latest version if needed
INSTALL_DIR="/home/cdsw/opensearch-app"

# Create the installation directory if it doesn't exist
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Download and extract OpenSearch
curl -O https://artifacts.opensearch.org/releases/bundle/opensearch/${OPENSEARCH_VER}/opensearch-${OPENSEARCH_VER}-linux-x64.tar.gz
tar -xzf opensearch-${OPENSEARCH_VER}-linux-x64.tar.gz

# Set up permissions
chown -R cdsw:cdsw opensearch-${OPENSEARCH_VER}
chmod -R 755 opensearch-${OPENSEARCH_VER}

# Set JAVA_HOME if not already set
export JAVA_HOME=${JAVA_HOME:-"/usr/lib/jvm/java-11-openjdk"}
echo "Using JAVA_HOME: $JAVA_HOME"

# Ensure OpenSearch starts in the background with security disabled (for testing only)
echo "Installation complete. Use run_opensearch.sh to start the service."
