"""
Configuration for Printavo API, SSActivewear API, Sanmar API, and Claude AI API
"""
import os
import json
from pathlib import Path

# API Configuration
PRINTAVO_API_ENDPOINT = "https://www.printavo.com/api/v2"
SSACTIVEWEAR_API_ENDPOINT = "https://api.ssactivewear.com/v2"

# Sanmar SOAP API WSDLs
SANMAR_PRODUCTION_WSDL = "https://ws.sanmar.com:8080/SanMarWebService/SanMarProductInfoServicePort?wsdl"
SANMAR_STAGE_WSDL = "https://stage-ws.sanmar.com:8080/SanMarWebService/SanMarProductInfoServicePort?wsdl"

# Config file location (in user's home directory)
CONFIG_DIR = Path.home() / ".printavo_quote_creator"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Global variables for credentials
PRINTAVO_EMAIL = None
PRINTAVO_TOKEN = None
SSACTIVEWEAR_ACCOUNT = None
SSACTIVEWEAR_API_KEY = None
SANMAR_CUSTOMER_NUMBER = None
SANMAR_USERNAME = None
SANMAR_PASSWORD = None
SANMAR_USE_PRODUCTION = False  # Default to staging for safety
CLAUDE_API_KEY = None  # NEW


def load_credentials():
    """Load credentials from config file or environment variables"""
    global PRINTAVO_EMAIL, PRINTAVO_TOKEN
    global SSACTIVEWEAR_ACCOUNT, SSACTIVEWEAR_API_KEY
    global SANMAR_CUSTOMER_NUMBER, SANMAR_USERNAME, SANMAR_PASSWORD, SANMAR_USE_PRODUCTION
    global CLAUDE_API_KEY

    # Try loading from config file first
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                PRINTAVO_EMAIL = config.get('email')
                PRINTAVO_TOKEN = config.get('token')
                SSACTIVEWEAR_ACCOUNT = config.get('ssactivewear_account')
                SSACTIVEWEAR_API_KEY = config.get('ssactivewear_api_key')
                SANMAR_CUSTOMER_NUMBER = config.get('sanmar_customer_number')
                SANMAR_USERNAME = config.get('sanmar_username')
                SANMAR_PASSWORD = config.get('sanmar_password')
                SANMAR_USE_PRODUCTION = config.get('sanmar_use_production', False)
                CLAUDE_API_KEY = config.get('claude_api_key')  # NEW
                return
        except Exception:
            pass

    # Fall back to environment variables
    PRINTAVO_EMAIL = os.getenv("PRINTAVO_EMAIL")
    PRINTAVO_TOKEN = os.getenv("PRINTAVO_TOKEN")
    SSACTIVEWEAR_ACCOUNT = os.getenv("SSACTIVEWEAR_ACCOUNT")
    SSACTIVEWEAR_API_KEY = os.getenv("SSACTIVEWEAR_API_KEY")
    SANMAR_CUSTOMER_NUMBER = os.getenv("SANMAR_CUSTOMER_NUMBER")
    SANMAR_USERNAME = os.getenv("SANMAR_USERNAME")
    SANMAR_PASSWORD = os.getenv("SANMAR_PASSWORD")
    SANMAR_USE_PRODUCTION = os.getenv("SANMAR_USE_PRODUCTION", "false").lower() == "true"
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")  # NEW


def save_credentials(email: str, token: str, ss_account: str = None, ss_api_key: str = None,
                     sanmar_customer: str = None, sanmar_user: str = None, sanmar_pass: str = None,
                     sanmar_production: bool = None, claude_api_key: str = None):  # NEW parameter
    """Save credentials to config file"""
    global PRINTAVO_EMAIL, PRINTAVO_TOKEN
    global SSACTIVEWEAR_ACCOUNT, SSACTIVEWEAR_API_KEY
    global SANMAR_CUSTOMER_NUMBER, SANMAR_USERNAME, SANMAR_PASSWORD, SANMAR_USE_PRODUCTION
    global CLAUDE_API_KEY

    # Create config directory if it doesn't exist
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing config if it exists
    config = {}
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        except Exception:
            pass

    # Update with new values
    config['email'] = email
    config['token'] = token

    if ss_account is not None:
        config['ssactivewear_account'] = ss_account
    if ss_api_key is not None:
        config['ssactivewear_api_key'] = ss_api_key

    if sanmar_customer is not None:
        config['sanmar_customer_number'] = sanmar_customer
    if sanmar_user is not None:
        config['sanmar_username'] = sanmar_user
    if sanmar_pass is not None:
        config['sanmar_password'] = sanmar_pass
    if sanmar_production is not None:
        config['sanmar_use_production'] = sanmar_production

    if claude_api_key is not None:  # NEW
        config['claude_api_key'] = claude_api_key

    # Save to file
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

    # Set file permissions to be readable only by owner (security)
    os.chmod(CONFIG_FILE, 0o600)

    # Update global variables
    PRINTAVO_EMAIL = email
    PRINTAVO_TOKEN = token
    if ss_account is not None:
        SSACTIVEWEAR_ACCOUNT = ss_account
    if ss_api_key is not None:
        SSACTIVEWEAR_API_KEY = ss_api_key
    if sanmar_customer is not None:
        SANMAR_CUSTOMER_NUMBER = sanmar_customer
    if sanmar_user is not None:
        SANMAR_USERNAME = sanmar_user
    if sanmar_pass is not None:
        SANMAR_PASSWORD = sanmar_pass
    if sanmar_production is not None:
        SANMAR_USE_PRODUCTION = sanmar_production
    if claude_api_key is not None:  # NEW
        CLAUDE_API_KEY = claude_api_key


def make_headers() -> dict:
    """Generate headers for Printavo API requests"""
    return {
        "Content-Type": "application/json",
        "email": PRINTAVO_EMAIL,
        "token": PRINTAVO_TOKEN
    }


def validate_credentials() -> tuple[bool, str]:
    """Validate that Printavo credentials are set"""
    if PRINTAVO_EMAIL and PRINTAVO_TOKEN:
        source = "config file" if CONFIG_FILE.exists() else "environment variables"
        return True, f"✓ Printavo credentials loaded from {source}: {PRINTAVO_EMAIL}"
    return False, "✗ Missing Printavo credentials! Please enter them in Settings."


def validate_ssactivewear_credentials() -> tuple[bool, str]:
    """Validate that SSActivewear credentials are set"""
    if SSACTIVEWEAR_ACCOUNT and SSACTIVEWEAR_API_KEY:
        return True, f"✓ SSActivewear credentials configured (Account: {SSACTIVEWEAR_ACCOUNT})"
    return False, "⚠ SSActivewear credentials not set. Product descriptions won't be auto-filled."


def validate_sanmar_credentials() -> tuple[bool, str]:
    """Validate that Sanmar credentials are set"""
    if SANMAR_CUSTOMER_NUMBER and SANMAR_USERNAME and SANMAR_PASSWORD:
        env = "Production" if SANMAR_USE_PRODUCTION else "Staging"
        return True, f"✓ Sanmar credentials configured (Customer: {SANMAR_CUSTOMER_NUMBER}, Env: {env})"
    return False, "⚠ Sanmar credentials not set. Sanmar product lookups won't work."


def validate_claude_credentials() -> tuple[bool, str]:  # NEW
    """Validate that Claude API credentials are set"""
    if CLAUDE_API_KEY:
        # Mask most of the key for security, show first 8 chars
        masked_key = CLAUDE_API_KEY[:8] + "..." if len(CLAUDE_API_KEY) > 8 else "***"
        return True, f"✓ Claude API configured ({masked_key})"
    return False, "⚠ Claude API key not set. AI processing will not work."


# Load credentials on import
load_credentials()