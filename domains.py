"""
Google Workspace domain management script for adding domain aliases.

This module provides functionality to bulk add domain aliases to a
Google Workspace account using the Admin SDK Directory API.
"""

import asyncio
import csv
import os

import aiohttp
from google.auth.transport.requests import Request
from google.oauth2 import service_account

# Configuration
SCOPES = ["https://www.googleapis.com/auth/admin.directory.domain"]
API_URL = "https://admin.googleapis.com/admin/directory/v1/customer/my_customer/domains"


class CredentialsManager:
    """Manages Google service account credentials with caching and reset capability.
    
    This class provides a more robust approach to credential management than
    module-level globals, making it easier to test and manage multiple credential sets.
    """
    
    def __init__(self):
        self._credentials = None
    
    def get_credentials(self):
        """Load and return Google service account credentials."""
        if self._credentials is None:
            service_account_file = os.environ.get(
                "GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json"
            )
            if not os.path.exists(service_account_file):
                raise FileNotFoundError(
                    f"Service account file not found: {service_account_file}. "
                    f"Set GOOGLE_SERVICE_ACCOUNT_FILE environment variable to specify the path."
                )
            self._credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=SCOPES
            )
        return self._credentials
    
    def get_access_token(self):
        """Fetches OAuth 2.0 access token for API requests."""
        credentials = self.get_credentials()
        # Refresh the token if it's expired or not yet obtained
        if not credentials.valid:
            credentials.refresh(Request())
        return credentials.token
    
    def reset(self):
        """Reset cached credentials. Useful for testing or credential rotation."""
        self._credentials = None


# Default credentials manager instance
_credentials_manager = CredentialsManager()


def get_credentials():
    """Load and return Google service account credentials.
    
    This is a convenience function that uses the default credentials manager.
    For more control, use CredentialsManager directly.
    """
    return _credentials_manager.get_credentials()


def get_access_token():
    """Fetches OAuth 2.0 access token for API requests.
    
    This is a convenience function that uses the default credentials manager.
    For more control, use CredentialsManager directly.
    """
    return _credentials_manager.get_access_token()


def reset_credentials():
    """Reset cached credentials. Useful for testing or credential rotation."""
    _credentials_manager.reset()


async def add_domain_alias(session, alias_domain, primary_domain):
    """Async function to add a domain alias."""
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
    }
    payload = {
        "domainAlias": True,
        "domainName": alias_domain,
        "parentDomainName": primary_domain,
    }

    async with session.post(API_URL, headers=headers, json=payload) as response:
        if response.status == 200:
            print(f"✅ Successfully added: {alias_domain}")
        else:
            error_text = await response.text()
            print(f"❌ Failed to add {alias_domain}: {error_text}")


async def bulk_upload_domains(csv_path):
    """Reads domains from CSV and adds them asynchronously."""
    async with aiohttp.ClientSession() as session:
        tasks = []
        with open(csv_path, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                task = add_domain_alias(
                    session, row["alias_domain"], row["primary_domain"]
                )
                tasks.append(task)

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    csv_file = (
        "domains.csv"  # CSV file with 'alias_domain' and 'primary_domain' columns
    )
    asyncio.run(bulk_upload_domains(csv_file))
