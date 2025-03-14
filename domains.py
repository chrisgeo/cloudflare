import csv
import aiohttp
import asyncio
from google.oauth2 import service_account

# Configuration
SCOPES = ['https://www.googleapis.com/auth/admin.directory.domain']
SERVICE_ACCOUNT_FILE = 'service_account.json'  # Replace with your service account JSON key file
API_URL = "https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains"

# Authenticate with Google Admin SDK
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

async def get_access_token():
    """Fetches OAuth 2.0 access token for API requests."""
    request = credentials.with_scopes(SCOPES)
    return request.token

async def add_domain_alias(session, alias_domain, primary_domain):
    """Async function to add a domain alias."""
    headers = {
        'Authorization': f'Bearer {await get_access_token()}',
        'Content-Type': 'application/json'
    }
    payload = {
        "domainAlias": True,
        "domainName": alias_domain,
        "parentDomainName": primary_domain
    }

    async with session.post(API_URL, headers=headers, json=payload) as response:
        if response.status == 200:
            print(f"✅ Successfully added: {alias_domain}")
        else:
            error_text = await response.text()
            print(f"❌ Failed to add {alias_domain}: {error_text}")

async def bulk_upload_domains(csv_file):
    """Reads domains from CSV and adds them asynchronously."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        with open(csv_file, newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                task = add_domain_alias(session, row['alias_domain'], row['primary_domain'])
                tasks.append(task)

        await asyncio.gather(*tasks)

if __name__ == "__main__":
    csv_file = "domains.csv"  # CSV file with 'alias_domain' and 'primary_domain' columns
    asyncio.run(bulk_upload_domains(csv_file))
