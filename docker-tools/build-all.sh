#!/bin/bash
# Build and verify all security tool Docker images

set -euo pipefail  # Exit on error, unset var, or pipe failure

echo "========================================="
echo "Building all security tool Docker images"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

TOOLS=("sublist3r" "httpx" "gobuster" "zap" "nuclei" "sqlmap")
IMAGES=(
    "security-tools:sublist3r"
    "security-tools:httpx"
    "security-tools:gobuster"
    "security-tools:zap"
    "security-tools:nuclei"
    "security-tools:sqlmap"
)

# Mapping of verification commands per tool
VERIFY_COMMANDS=(
    "python3 sublist3r.py -h"
    "/app/httpx -h"
    "/app/gobuster -h"
    "/app/zap-baseline.py -h"
    "/app/nuclei -version"
    "python3 sqlmap.py -h"
)

# Function to build an image
build_image() {
    local tool_dir=$1
    local image_name=$2
    
    echo -e "${YELLOW}Building ${tool_dir}...${NC}"
    pushd "$tool_dir" >/dev/null
    
    if docker build -t "$image_name" .; then
        echo -e "${GREEN}✓ ${tool_dir} built successfully${NC}"
        popd >/dev/null
        return 0
    else
        echo -e "${RED}✗ Failed to build ${tool_dir}${NC}"
        popd >/dev/null
        return 1
    fi
}

# Function to verify an image by running a lightweight command
verify_image() {
    local image_name=$1
    local verify_cmd=$2
    
    echo -e "${BLUE}↳ Verifying ${image_name} (${verify_cmd})${NC}"
    if docker run --rm "$image_name" $verify_cmd >/dev/null 2>&1; then
        echo -e "${GREEN}  ✔ ${image_name} verification passed${NC}"
        return 0
    else
        echo -e "${RED}  ✖ ${image_name} verification failed${NC}"
        return 1
    fi
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Store the original directory
ORIGINAL_DIR=$(pwd)

# Build and verify all images
BUILD_FAILED=0

for i in "${!TOOLS[@]}"; do
    TOOL="${TOOLS[$i]}"
    IMAGE="${IMAGES[$i]}"
    VERIFY_CMD="${VERIFY_COMMANDS[$i]}"
    
    build_image "$TOOL" "$IMAGE" || BUILD_FAILED=1
    echo ""
    
    if ! verify_image "$IMAGE" "$VERIFY_CMD"; then
        BUILD_FAILED=1
    fi
    echo ""
done

# Return to original directory
cd "$ORIGINAL_DIR"

# Summary
if [ $BUILD_FAILED -eq 0 ]; then
    echo "========================================="
    echo -e "${GREEN}All images built and verified successfully!${NC}"
    echo "========================================="
    echo ""
    echo "Built images:"
    docker images | grep "security-tools" || echo "No security-tools images found"
    exit 0
else
    echo "========================================="
    echo -e "${RED}Some builds failed. Please check the errors above.${NC}"
    echo "========================================="
    exit 1
fi


