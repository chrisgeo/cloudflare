#!/usr/bin/env python3
"""Fetch all domains from Cloudflare using Global API Key."""

import json
import os
from cloudflare import Cloudflare, APIStatusError, APIError, APIConnectionError

# Cloudflare API Configuration


def get_all_domains():
    """Fetch all domains using the CloudFlare package."""
    cf = Cloudflare(api_token=os.environ.get("CLOUDFLARE_API_TOKEN"))

    try:
        # The CloudFlare package handles pagination automatically
        zones = cf.zones.list()

        return [domain.name for domain in zones]

    except APIStatusError as e:
        print(f"❌ Error fetching domains: {e}")
    except APIConnectionError as e:
        print(f"❌ Connection error: {e}")
    except APIError as e:
        print(f"❌ Internal Cloudflare error: {e}")

    return []


def save_domains_to_json(domains, json_file="cloudflare_domains.json"):
    """Save the domains to a JSON file."""
    with open(json_file, "w", encoding="utf-8") as file:
        json.dump(domains, file, indent=4)
    print(f"✅ Domains saved to {json_file}")


def main():
    """
    Main entry point for the script.

    Fetches all domains from Cloudflare and saves them to a JSON file.
    If no domains are found, prints a message indicating so.
    """
    domains = get_all_domains()
    if domains:
        save_domains_to_json(domains)
    else:
        print("❗ No domains found in your Cloudflare account.")


if __name__ == "__main__":
    main()
