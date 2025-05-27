# Cloudflare & Google Workspace Domain Management Tools

This repository contains Python scripts for managing domains in Cloudflare and Google Workspace. It provides tools to fetch all domains from your Cloudflare account and bulk add domain aliases to Google Workspace.

## Project Overview

This project includes multiple approaches for domain management:

- **Cloudflare Domain Fetching**: Two different implementations to retrieve all domains from your Cloudflare account
- **Google Workspace Domain Management**: Bulk add domain aliases to Google Workspace using the Admin SDK
- **Docker Support**: Containerized execution with Docker Compose

## Files Description

### Core Scripts

- **`cloudflare_domains.py`** - Asynchronous script using direct Cloudflare API calls with aiohttp to fetch all domains and save them to JSON
- **`cloudflare_domains_global_key.py`** - Alternative implementation using the official Cloudflare Python SDK for domain fetching - uses global API Key
- **`domains.py`** - Google Workspace domain alias management script using Admin SDK Directory API
- **`cloudflare_domains.json`** - Sample output file containing fetched domain names

### Configuration Files

- **`requirements.txt`** - Python dependencies (cloudflare, aiohttp, google-auth)
- **`compose.yml`** - Docker Compose configuration for containerized execution
- **`entrypoint.sh`** - Docker container entry point script
- **`.gitignore`** - Git ignore patterns for cache files, logs, and sensitive data

## Environment Variables

### Required Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# Cloudflare API Configuration
CLOUDFLARE_API_TOKEN=your_cloudflare_api_token_here
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id_here

# Google Workspace Configuration (for domains.py)
GOOGLE_SERVICE_ACCOUNT_FILE=path/to/service_account.json
```

### Getting Cloudflare Credentials

1. **API Token**: Go to [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens) → Create Token → Custom Token
   - Permissions: `Zone:Read` for all zones
   - Account Resources: Include your account

2. **Account ID**: Found in the right sidebar of your Cloudflare Dashboard

### Google Workspace Setup (for domains.py)

1. Create a service account in Google Cloud Console
2. Enable the Admin SDK Directory API
3. Download the service account JSON key file
4. Set up domain-wide delegation for the service account
5. Create a `domains.csv` file with columns: `alias_domain`, `primary_domain`

## Installation & Usage

### Local Installation

```bash
# Clone the repository
git clone <repository-url>
cd cloudflare

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Edit with your actual credentials
```

### Running the Scripts

#### Fetch Cloudflare Domains (Method 1 - Direct API)

```bash
# Edit cloudflare_domains.py to add your credentials directly, or use environment variables
python cloudflare_domains.py
```

#### Fetch Cloudflare Domains (Method 2 - SDK)

```bash
export CLOUDFLARE_API_TOKEN="your_token_here"
python cloudflare_domains_global_key.py
```

#### Google Workspace Domain Management

```bash
# Ensure service_account.json and domains.csv are in place
python domains.py
```

### Docker Usage

```bash
# Run with Docker Compose
docker-compose up

# Or build and run manually
docker build -t cloudflare-domains .
docker run --env-file .env -v $(pwd):/app cloudflare-domains
```

## Output

- **`cloudflare_domains.json`** - Contains all domains from your Cloudflare account in JSON format
- Console output shows success/error messages for each operation

## Security Notes

- Never commit `.env` files or API tokens to version control
- The `.gitignore` file excludes sensitive files like `.env` and `*.json`
- Use environment variables or secure secret management in production
- Ensure proper Google Workspace permissions for domain management

## Dependencies

- `cloudflare` - Official Cloudflare Python SDK
- `aiohttp` - Async HTTP client for API requests
- `google-auth` - Google authentication library for Workspace APIs
