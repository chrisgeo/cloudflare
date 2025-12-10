#!/bin/sh
set -e  # Exit on error
pip install --no-cache-dir -r requirements.txt
python cloudflare_domains_global_key.py
