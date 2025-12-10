import asyncio
import json
import os

import aiohttp


def get_api_config():
    """Get Cloudflare API configuration from environment variables."""
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")

    if not api_token:
        raise ValueError("CLOUDFLARE_API_TOKEN environment variable is required")
    if not account_id:
        raise ValueError("CLOUDFLARE_ACCOUNT_ID environment variable is required")

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
