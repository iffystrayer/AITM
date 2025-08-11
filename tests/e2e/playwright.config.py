"""
Playwright configuration for end-to-end authorization tests.
"""

import os
from playwright.async_api import async_playwright

# Test configuration
TEST_CONFIG = {
    "base_url": os.getenv("BASE_URL", "http://localhost:8000"),
    "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:3000"),
    "headless": os.getenv("HEADLESS", "true").lower() == "true",
    "timeout": int(os.getenv("TEST_TIMEOUT", "30000")),  # 30 seconds
    "browser": os.getenv("BROWSER", "chromium"),  # chromium, firefox, webkit
}

# Browser configuration
BROWSER_CONFIG = {
    "headless": TEST_CONFIG["headless"],
    "args": [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-web-security",
        "--allow-running-insecure-content"
    ] if os.getenv("CI") else []
}

# Context configuration
CONTEXT_CONFIG = {
    "viewport": {"width": 1280, "height": 720},
    "ignore_https_errors": True,
    "accept_downloads": True,
    "record_video_dir": "tests/e2e/videos" if os.getenv("RECORD_VIDEO") else None,
    "record_har_path": "tests/e2e/har/test.har" if os.getenv("RECORD_HAR") else None
}

def get_test_config():
    """Get the test configuration"""
    return TEST_CONFIG

def get_browser_config():
    """Get the browser configuration"""
    return BROWSER_CONFIG

def get_context_config():
    """Get the context configuration"""
    return CONTEXT_CONFIG