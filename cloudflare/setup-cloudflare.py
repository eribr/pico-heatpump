#!/usr/bin/env python3
"""
Cloudflare Proxy Setup - Python Alternative
More portable than shell scripts, works on Windows/Mac/Linux
"""

import os
import sys
import json
import requests
from typing import Optional, Dict
from pathlib import Path

class CloudflareProxySetup:
    """Setup Cloudflare proxy to hide internal server"""
    
    BASE_URL = "https://api.cloudflare.com/client/v4"
    
    def __init__(self, api_token: str, zone_id: str):
        self.api_token = api_token
        self.zone_id = zone_id
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        })
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make API request"""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            if method == "GET":
                response = self.session.get(url)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "PUT":
                response = self.session.put(url, json=data)
            elif method == "PATCH":
                response = self.session.patch(url, json=data)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API Error: {e}")
            if hasattr(e.response, 'text'):
                print(f"   Response: {e.response.text}")
            sys.exit(1)
    
    def create_or_update_dns_record(self, subdomain: str, origin: str, 
                                     origin_port: int = 66443) -> str:
        """Create or update proxied DNS record"""
        full_domain = f"{subdomain}.bergfur.se"  # Adjust zone as needed
        
        print(f"Setting up DNS record: {full_domain} → {origin}:{origin_port} (proxied)")
        
        # Check existing record
        records_resp = self._request(
            "GET",
            f"zones/{self.zone_id}/dns_records?name={full_domain}"
        )
        
        record_data = {
            "type": "CNAME",
            "name": full_domain,
            "content": origin,
            "ttl": 3600,
            "proxied": True,
            "comment": f"Cloudflare proxy hiding {origin}:{origin_port}"
        }
        
        if records_resp.get("result") and len(records_resp["result"]) > 0:
            # Update existing
            record_id = records_resp["result"][0]["id"]
            print(f"Updating existing record ID: {record_id}")
            result = self._request("PUT", 
                f"zones/{self.zone_id}/dns_records/{record_id}",
                record_data)
        else:
            # Create new
            print("Creating new DNS record")
            result = self._request("POST",
                f"zones/{self.zone_id}/dns_records",
                record_data)
        
        if result.get("success"):
            record_id = result["result"]["id"]
            print(f"✓ DNS record configured (ID: {record_id})")
            return record_id
        else:
            print(f"❌ Failed to setup DNS record")
            print(json.dumps(result, indent=2))
            sys.exit(1)
    
    def configure_ssl_tls(self):
        """Configure SSL/TLS settings"""
        print("Configuring SSL/TLS settings...")
        
        result = self._request("PATCH",
            f"zones/{self.zone_id}/settings/ssl",
            {"value": "full"})
        
        if result.get("success"):
            print("✓ SSL/TLS set to Full mode")
        else:
            print("⚠ Could not configure SSL/TLS (may require certain plan)")
    
    def enable_https_redirect(self):
        """Always redirect HTTP to HTTPS"""
        print("Enabling HTTPS enforcement...")
        
        result = self._request("PATCH",
            f"zones/{self.zone_id}/settings/always_use_https",
            {"value": "on"})
        
        if result.get("success"):
            print("✓ HTTPS redirect enabled")
        else:
            print("⚠ Could not enable HTTPS redirect")
    
    def setup(self, subdomain: str, origin: str, origin_port: int = 66443):
        """Run full setup"""
        print("\n" + "="*60)
        print("  Cloudflare Free Proxy Setup")
        print("="*60 + "\n")
        
        try:
            self.create_or_update_dns_record(subdomain, origin, origin_port)
            self.configure_ssl_tls()
            self.enable_https_redirect()
            
            print("\n" + "="*60)
            print("✓ Setup Complete!")
            print("="*60)
            print(f"\nConfiguration:")
            print(f"  Public Domain:    {subdomain}.bergfur.se")
            print(f"  Origin Server:    {origin}:{origin_port}")
            print(f"  Proxying:         Enabled (Orange Cloud)")
            print(f"\nNext Steps:")
            print(f"  1. Verify DNS: nslookup {subdomain}.bergfur.se")
            print(f"  2. Test HTTPS: curl https://{subdomain}.bergfur.se")
            print(f"  3. Firewall: Restrict origin to Cloudflare IPs")
            print(f"     See: https://www.cloudflare.com/ips/\n")
    
        except Exception as e:
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)

def load_config() -> Dict:
    """Load configuration from config.json or environment"""
    config_file = "config.json"
    
    # Try to load from config.json first
    if Path(config_file).exists():
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                print(f"✓ Loaded configuration from {config_file}")
                return config
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {config_file}: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading {config_file}: {e}")
            sys.exit(1)
    
    # Fall back to environment variables
    print("⚠ config.json not found, using environment variables")
    api_token = os.getenv("CLOUDFLARE_API_TOKEN")
    zone_id = os.getenv("CLOUDFLARE_ZONE_ID")
    
    if not api_token:
        print("Error: CLOUDFLARE_API_TOKEN environment variable not set")
        print("Get token at: https://dash.cloudflare.com/profile/api-tokens")
        sys.exit(1)
    
    if not zone_id:
        print("Error: CLOUDFLARE_ZONE_ID environment variable not set")
        print("Find Zone ID in: https://dash.cloudflare.com/ → Domain Overview")
        sys.exit(1)
    
    return {
        "cloudflare": {
            "api_token": api_token,
            "zone_id": zone_id
        },
        "proxy": {
            "subdomain": "oland",
            "origin": "bergfur.dyndns.org",
            "origin_port": 66443
        }
    }

def main():
    """Main entry point"""
    config = load_config()
    
    # Extract Cloudflare credentials
    cf_config = config.get("cloudflare", {})
    api_token = cf_config.get("api_token")
    zone_id = cf_config.get("zone_id")
    
    if not api_token or not zone_id:
        print("Error: Missing Cloudflare API token or Zone ID in configuration")
        sys.exit(1)
    
    # Extract proxy configuration
    proxy_config = config.get("proxy", {})
    subdomain = proxy_config.get("subdomain", "oland")
    origin = proxy_config.get("origin", "bergfur.dyndns.org")
    origin_port = proxy_config.get("origin_port", 66443)
    
    # Run setup
    setup = CloudflareProxySetup(api_token, zone_id)
    setup.setup(subdomain, origin, origin_port)

if __name__ == "__main__":
    main()
