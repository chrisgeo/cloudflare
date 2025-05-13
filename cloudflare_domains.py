import asyncio
import json

import aiohttp

# Cloudflare API Configuration
API_TOKEN = "YOUR_CLOUDFLARE_ACCOUNT_API_TOKEN"  # Use your Account Token
ACCOUNT_ID = "YOUR_CLOUDFLARE_ACCOUNT_ID"  # Account ID is required for Account Tokens
BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/zones"

# Headers for authentication
HEADERS = {"Authorization": f"Bearer {API_TOKEN}", "Content-Type": "application/json"}


async def fetch_domains(session, page=1, per_page=50):
    """Fetch domains from Cloudflare with pagination."""
    async with session.get(
        BASE_URL, headers=HEADERS, params={"page": page, "per_page": per_page}
    ) as response:
        data = await response.json()
        if data.get("success"):
            return data.get("result", [])
        else:
            print(f"❌ Error fetching page {page}: {data}")
            return []


async def get_all_domains():
    """Fetch all domains asynchronously."""
    async with aiohttp.ClientSession() as session:
        all_domains = []
        page = 1
        while True:
            domains = await fetch_domains(session, page)
            if not domains:
                break
            all_domains.extend(domains)
            page += 1
        return all_domains


async def save_domains_to_json(domains, json_file="cloudflare_domains.json"):
    """Save the domains to a JSON file."""
    with open(json_file, "w", encoding="utf-8") as file:
        json.dump(domains, file, indent=4)
    print(f"✅ Domains saved to {json_file}")


async def main():
    domains = await get_all_domains()
    if domains:
        await save_domains_to_json(domains)
    else:
        print("❗ No domains found in your Cloudflare account.")


if __name__ == "__main__":
    asyncio.run(main())
