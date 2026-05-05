import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv(".env")

BASE_URL = "https://api.hetzner.cloud/v1"
DYNDNS_TTL = 7200


def get_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def get_external_ip() -> str:
    response = requests.get("https://ipv4.icanhazip.com")
    if response.status_code != 200:
        print("Error retrieving external IP. Check your internet connection.")
        sys.exit(1)
    return response.text.strip()


def get_zone_id(api_key: str, dns_zone: str) -> str:
    response = requests.get(
        f"{BASE_URL}/zones?name={dns_zone}", headers=get_headers(api_key)
    )
    zones: list[dict] = response.json().get("zones", [])
    if not zones:
        print(f"Zone '{dns_zone}' not found. Check DNS_ZONE in .env.")
        sys.exit(1)
    return str(zones[0]["id"])


def get_rrsets(api_key: str, zone_id: str) -> list[dict]:
    response = requests.get(
        f"{BASE_URL}/zones/{zone_id}/rrsets", headers=get_headers(api_key)
    )
    if response.status_code != 200:
        print(f"Error retrieving RRsets: {response.status_code} {response.text}")
        sys.exit(1)
    return list(response.json().get("rrsets", []))


def find_rrset(rrsets: list[dict], name: str) -> str:
    """Returns current IP for matching A record, or '' if not found."""
    for rrset in rrsets:
        if rrset["name"] == name and rrset["type"] == "A":
            records: list[dict] = rrset["records"]
            return str(records[0]["value"]) if records else ""
    return ""


def delete_rrset(api_key: str, zone_id: str, name: str) -> bool:
    response = requests.delete(
        f"{BASE_URL}/zones/{zone_id}/rrsets/{name}/A",
        headers=get_headers(api_key),
    )
    if response.status_code not in (200, 201, 204):
        print(f"{name}: Failed to delete RRset: {response.status_code} {response.text}")
        return False
    return True


def create_rrset(api_key: str, zone_id: str, name: str, ip: str) -> bool:
    response = requests.post(
        f"{BASE_URL}/zones/{zone_id}/rrsets",
        headers=get_headers(api_key),
        json={"name": name, "type": "A", "ttl": DYNDNS_TTL, "records": [{"value": ip}]},
    )
    if response.status_code not in (200, 201):
        print(f"{name}: Failed to create RRset: {response.status_code} {response.text}")
        return False
    return True


def main() -> None:
    dns_zone = os.getenv("DNS_ZONE")
    raw_names = os.getenv("DYNDNS_NAMES")
    api_key = os.getenv("API_KEY")

    if not dns_zone or not raw_names or not api_key:
        print("Missing required environment variables. Check your .env file.")
        sys.exit(1)

    # Pylance now knows these are str, not str | None
    dyndns_names: list[str] = raw_names.split(",")

    external_ip = get_external_ip()
    zone_id = get_zone_id(api_key, dns_zone)
    rrsets = get_rrsets(api_key, zone_id)

    for name in dyndns_names:
        name = name.strip()
        current_ip = find_rrset(rrsets, name)

        if current_ip == external_ip:
            print(f"{name}: IP unchanged ({external_ip}). No update necessary.")
            continue

        if current_ip:
            print(f"Updating IP for {name}: {current_ip} → {external_ip}")
            if not delete_rrset(api_key, zone_id, name):
                continue
        else:
            print(f"Creating new A record for {name}...")

        create_rrset(api_key, zone_id, name, external_ip)


if __name__ == "__main__":
    main()
