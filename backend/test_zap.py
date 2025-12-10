#!/usr/bin/env python3
"""
Test script to verify ZAP Docker container is working correctly
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.docker.client import docker_client
from app.docker.tools import ZAPTool
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_zap_image_exists():
    """Test if ZAP image exists"""
    logger.info("Testing if ZAP Docker image exists...")
    zap_tool = ZAPTool()
    
    if docker_client.image_exists(zap_tool.image):
        logger.info(f"✓ ZAP image '{zap_tool.image}' exists")
        return True
    else:
        logger.error(f"✗ ZAP image '{zap_tool.image}' not found")
        logger.error(f"  Please build it using: cd docker-tools/zap && docker build -t {zap_tool.image} .")
        return False

def test_zap_scan_localhost():
    """Test ZAP scan on a localhost URL"""
    logger.info("\nTesting ZAP scan on localhost:5000...")
    zap_tool = ZAPTool()
    
    # Test with a simple localhost URL
    test_url = "http://localhost:5000"
    logger.info(f"Running ZAP scan on {test_url}...")
    
    try:
        result = zap_tool.run(test_url, is_localhost=True)
        
        logger.info(f"\nZAP Scan Results:")
        logger.info(f"  Status: {result.get('status')}")
        logger.info(f"  Exit Code: {result.get('exit_code')}")
        logger.info(f"  Alert Count: {result.get('alert_count', 0)}")
        
        if result.get('error'):
            logger.error(f"  Error: {result.get('error')}")
        
        if result.get('alerts'):
            logger.info(f"  Alerts found:")
            for i, alert in enumerate(result.get('alerts', [])[:5], 1):  # Show first 5
                logger.info(f"    {i}. {alert.get('name')} - Risk: {alert.get('risk')}")
        
        if result.get('status') == 'failed':
            logger.error("✗ ZAP scan failed")
            if result.get('raw_output'):
                logger.error(f"  Raw output (first 500 chars):\n{result.get('raw_output')[:500]}")
            return False
        else:
            logger.info("✓ ZAP scan completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"✗ ZAP scan error: {e}", exc_info=True)
        return False

def test_zap_scan_external():
    """Test ZAP scan on an external URL (like example.com)"""
    logger.info("\nTesting ZAP scan on external URL (example.com)...")
    zap_tool = ZAPTool()
    
    test_url = "http://example.com"
    logger.info(f"Running ZAP scan on {test_url}...")
    
    try:
        result = zap_tool.run(test_url, is_localhost=False)
        
        logger.info(f"\nZAP Scan Results:")
        logger.info(f"  Status: {result.get('status')}")
        logger.info(f"  Exit Code: {result.get('exit_code')}")
        logger.info(f"  Alert Count: {result.get('alert_count', 0)}")
        
        if result.get('error'):
            logger.warning(f"  Error: {result.get('error')}")
        
        if result.get('status') == 'failed':
            logger.error("✗ ZAP scan failed")
            return False
        else:
            logger.info("✓ ZAP scan completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"✗ ZAP scan error: {e}", exc_info=True)
        return False

def main():
    """Run all tests"""
    logger.info("=" * 60)
    logger.info("ZAP Docker Container Test Suite")
    logger.info("=" * 60)
    
    # Test 1: Check if image exists
    if not test_zap_image_exists():
        logger.error("\n❌ Test failed: ZAP image not found")
        logger.error("Please build the ZAP image first:")
        logger.error("  cd docker-tools/zap")
        logger.error("  docker build -t security-tools:zap .")
        return 1
    
    # Test 2: Test localhost scan (if localhost:5000 is available)
    logger.info("\n" + "=" * 60)
    logger.info("Note: localhost:5000 scan will fail if no service is running")
    logger.info("=" * 60)
    localhost_result = test_zap_scan_localhost()
    
    # Test 3: Test external scan
    logger.info("\n" + "=" * 60)
    external_result = test_zap_scan_external()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    logger.info(f"Image exists: ✓")
    logger.info(f"Localhost scan: {'✓' if localhost_result else '✗ (expected if no service on :5000)'}")
    logger.info(f"External scan: {'✓' if external_result else '✗'}")
    
    if external_result:
        logger.info("\n✅ ZAP is working correctly!")
        return 0
    else:
        logger.error("\n❌ ZAP tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

