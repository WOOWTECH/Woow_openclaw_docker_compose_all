#!/usr/bin/env python3
"""
Hermes - Cloudflare Tunnel Auto-Initialization Script
Fetches Account ID via zones, finds/creates tunnel, retrieves token,
configures tunnel route to hermes-webui-svc, and saves config.
"""

import json
import os
import sys
import base64
import requests

CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
TUNNEL_NAME = os.environ.get("TUNNEL_NAME", "hermes")
DOMAIN = os.environ.get("HERMES_DOMAIN", "hermes-woowtechmag.woowtech.io")
BASE_URL = "https://api.cloudflare.com/client/v4"

HEADERS = {
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json",
}


def api_get(path):
    resp = requests.get(f"{BASE_URL}{path}", headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def api_post(path, payload):
    resp = requests.post(f"{BASE_URL}{path}", headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()


def api_put(path, payload):
    resp = requests.put(f"{BASE_URL}{path}", headers=HEADERS, json=payload)
    resp.raise_for_status()
    return resp.json()


def main():
    if not CF_API_TOKEN:
        print("[ERROR] CF_API_TOKEN environment variable is not set.")
        print("  Usage: CF_API_TOKEN=<your-token> python3 init-cloudflare-hermes.py")
        sys.exit(1)

    print("=" * 60)
    print("  Hermes - Cloudflare Tunnel Initialization")
    print("=" * 60)

    # Step 1: Get Account ID via zones
    print("\n[1/5] Fetching Cloudflare Account ID via zones...")
    zones_data = api_get("/zones")
    zones = zones_data.get("result", [])
    if not zones:
        print("[ERROR] No zones found. Token may lack zone:read permission.")
        sys.exit(1)
    account_id = zones[0]["account"]["id"]
    account_name = zones[0]["account"]["name"]
    print(f"  -> Account: {account_name}")
    print(f"  -> Account ID: {account_id}")

    # Step 2: Find or create tunnel
    print(f"\n[2/5] Looking for tunnel '{TUNNEL_NAME}'...")
    tunnels_data = api_get(f"/accounts/{account_id}/cfd_tunnel?name={TUNNEL_NAME}&is_deleted=false")
    tunnels = tunnels_data.get("result", [])

    if tunnels:
        tunnel = tunnels[0]
        tunnel_id = tunnel["id"]
        print(f"  -> Found existing tunnel: {tunnel_id}")
    else:
        print(f"  -> Creating tunnel '{TUNNEL_NAME}'...")
        import secrets as sec
        tunnel_secret = base64.b64encode(sec.token_bytes(32)).decode()
        create_data = api_post(f"/accounts/{account_id}/cfd_tunnel", {
            "name": TUNNEL_NAME,
            "tunnel_secret": tunnel_secret,
        })
        tunnel_id = create_data["result"]["id"]
        print(f"  -> Created tunnel: {tunnel_id}")

    # Step 3: Get tunnel token
    print("\n[3/5] Fetching tunnel token...")
    token_data = api_get(f"/accounts/{account_id}/cfd_tunnel/{tunnel_id}/token")
    if token_data.get("success"):
        tunnel_token = token_data["result"]
        print(f"  -> Token obtained (length: {len(tunnel_token)})")
    else:
        print("[ERROR] Failed to retrieve tunnel token.")
        sys.exit(1)

    # Step 4: Configure tunnel ingress route → hermes-webui
    print(f"\n[4/5] Configuring tunnel route: {DOMAIN} → hermes-webui-svc:3000...")
    try:
        route_config = {
            "config": {
                "ingress": [
                    {
                        "hostname": DOMAIN,
                        "service": "http://hermes-webui-svc.hermes.svc.cluster.local:3000",
                    },
                    {
                        "service": "http_status:404",
                    },
                ]
            }
        }
        api_put(f"/accounts/{account_id}/cfd_tunnel/{tunnel_id}/configurations", route_config)
        print(f"  -> Route configured: {DOMAIN} → hermes-webui-svc:3000")
    except Exception as e:
        print(f"  [WARN] Route configuration failed: {e}")
        print("  You can configure routes manually in Cloudflare dashboard.")

    # Step 5: Save config
    config = {
        "CF_ACCOUNT_ID": account_id,
        "CF_TUNNEL_ID": tunnel_id,
        "CF_TUNNEL_TOKEN": tunnel_token,
        "CF_API_TOKEN": CF_API_TOKEN,
        "DOMAIN": DOMAIN,
        "TUNNEL_NAME": TUNNEL_NAME,
    }
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cf-config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n[5/5] Config saved to: {config_path}")
    print(f"  CF_ACCOUNT_ID   = {account_id}")
    print(f"  CF_TUNNEL_ID    = {tunnel_id}")
    print(f"  CF_TUNNEL_TOKEN = {tunnel_token[:30]}...")
    print(f"  DOMAIN          = {DOMAIN}")
    print("=" * 60)
    return config


if __name__ == "__main__":
    main()
