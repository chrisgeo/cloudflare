import asyncio
import configparser
import json
import os

import aiohttp

# Default paths for credentials files
DEFAULT_JSON_CREDENTIALS_FILE = "cloudflare_credentials.json"
DEFAULT_INI_CREDENTIALS_FILE = "cloudflare_credentials.ini"


def load_credentials_from_json(file_path):
    """Load credentials from a JSON file.

    Expected format:
    {
        "api_token": "your_token",
        "account_id": "your_account_id"
    }
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("api_token"), data.get("account_id")


def load_credentials_from_ini(file_path):
    """Load credentials from an INI file.

    Expected format:
    [cloudflare]
    api_token = your_token
    account_id = your_account_id
    """
    config = configparser.ConfigParser()
    config.read(file_path, encoding="utf-8")
    if "cloudflare" in config:
        return (
            config.get("cloudflare", "api_token", fallback=None),
            config.get("cloudflare", "account_id", fallback=None),
        )
    return None, None


def get_api_config():
    """Get Cloudflare API configuration.

    Configuration is loaded in the following order of precedence:
    1. JSON credentials file (cloudflare_credentials.json or CLOUDFLARE_CREDENTIALS_FILE env var)
    2. INI credentials file (cloudflare_credentials.ini or CLOUDFLARE_CREDENTIALS_FILE env var)
    3. Environment variables (CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID)
    """
    api_token = None
    account_id = None

    # Check for custom credentials file path from environment
    credentials_file = os.environ.get("CLOUDFLARE_CREDENTIALS_FILE")

    # Try loading from JSON file
    json_file = credentials_file if credentials_file and credentials_file.endswith(".json") else DEFAULT_JSON_CREDENTIALS_FILE
    if os.path.exists(json_file):
        try:
            api_token, account_id = load_credentials_from_json(json_file)
            if api_token and account_id:
                base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/zones"
                headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
                return base_url, headers
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️ Warning: Failed to parse JSON credentials file: {e}")

    # Try loading from INI file
    ini_file = credentials_file if credentials_file and credentials_file.endswith(".ini") else DEFAULT_INI_CREDENTIALS_FILE
    if os.path.exists(ini_file):
        try:
            api_token, account_id = load_credentials_from_ini(ini_file)
            if api_token and account_id:
                base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/zones"
                headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}
                return base_url, headers
        except configparser.Error as e:
            print(f"⚠️ Warning: Failed to parse INI credentials file: {e}")

    # Fall back to environment variables
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")

    if not api_token:
        raise ValueError(
            "Cloudflare API token not found. Provide it via:\n"
            "  - cloudflare_credentials.json file\n"
            "  - cloudflare_credentials.ini file\n"
            "  - CLOUDFLARE_API_TOKEN environment variable"
        )
    if not account_id:
        raise ValueError(
            "Cloudflare account ID not found. Provide it via:\n"
            "  - cloudflare_credentials.json file\n"
            "  - cloudflare_credentials.ini file\n"
            "  - CLOUDFLARE_ACCOUNT_ID environment variable"
        )

    base_url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/zones"
    headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

    return base_url, headers


async def fetch_domains(session, base_url, headers, page=1, per_page=50):
    """Fetch domains from Cloudflare with pagination."""
    async with session.get(
        base_url, headers=headers, params={"page": page, "per_page": per_page}
    ) as response:
        data = await response.json()
        if data.get("success"):
            return data.get("result", [])
        else:
            print(f"❌ Error fetching page {page}: {data}")
            return []


async def get_all_domains():
    """Fetch all domains asynchronously."""
    base_url, headers = get_api_config()

    async with aiohttp.ClientSession() as session:
        all_domains = []
        page = 1
        while True:
            domains = await fetch_domains(session, base_url, headers, page)
            if not domains:
                break
            all_domains.extend(domains)
            page += 1
        return all_domains


def save_domains_to_json(domains, json_file="cloudflare_domains.json"):
    """Save the domains to a JSON file."""
    with open(json_file, "w", encoding="utf-8") as file:
        json.dump(domains, file, indent=4)
    print(f"✅ Domains saved to {json_file}")


async def main():
    domains = await get_all_domains()
    if domains:
        save_domains_to_json(domains)
    else:
        print("❗ No domains found in your Cloudflare account.")


if __name__ == "__main__":
    asyncio.run(main())
