#!/bin/bash
# Master test script - runs all verification tests in sequence

echo "=========================================="
echo "  Bugbuster Scan Verification Tests"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Database Test
echo -e "${YELLOW}Step 1/3: Testing Database...${NC}"
python3 test_database.py
DB_RESULT=$?

if [ $DB_RESULT -ne 0 ]; then
    echo -e "${RED}❌ Database tests failed. Please fix database issues first.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Database tests passed${NC}"
echo ""

# Step 2: Tool Execution Test
echo -e "${YELLOW}Step 2/3: Testing Tool Execution...${NC}"
echo "This will test Docker connection and individual tools"
echo ""

python3 test_scan_execution.py
TOOL_RESULT=$?

if [ $TOOL_RESULT -ne 0 ]; then
    echo -e "${RED}❌ Tool execution tests failed.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Tool execution tests passed${NC}"
echo ""

# Step 3: Verify Scan Data
echo -e "${YELLOW}Step 3/3: Verifying Scan Data...${NC}"
python3 verify_scan_data.py

echo ""
echo -e "${GREEN}=========================================="
echo "  All Tests Complete!"
echo "==========================================${NC}"

