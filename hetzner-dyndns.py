import argparse
import os
import sys
import time
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

load_dotenv(".env")

BASE_URL = "https://api.hetzner.cloud/v1"
EXTERNAL_IP_URL = "https://ipv4.icanhazip.com"
DYNDNS_TTL = 7200
# Without a timeout a hanging request would block the --interval loop forever.
REQUEST_TIMEOUT = 10


class DyndnsError(Exception):
    """Expected failure with a message meant for the user, not a traceback."""


@dataclass(frozen=True)
class Config:
    dns_zone: str
    dyndns_names: list[str]
    api_key: str


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Hetzner DynDNS updater")
    parser.add_argument(
        "--interval",
        type=positive_int,
        metavar="SECONDS",
        help="repeat the update every SECONDS instead of running once",
    )
    return parser.parse_args(argv)


def load_config() -> Config:
    dns_zone = os.getenv("DNS_ZONE")
    raw_names = os.getenv("DYNDNS_NAMES")
    api_key = os.getenv("API_KEY")

    if not dns_zone or not raw_names or not api_key:
        raise DyndnsError(
            "Missing required environment variables. Check your .env file."
        )

    dyndns_names = [name.strip() for name in raw_names.split(",")]
    return Config(dns_zone, dyndns_names, api_key)


def get_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def get_external_ip() -> str:
    response = requests.get(EXTERNAL_IP_URL, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        raise DyndnsError(
            "Error retrieving external IP. Check your internet connection."
        )
    return response.text.strip()


def get_zone_id(api_key: str, dns_zone: str) -> str:
    response = requests.get(
        f"{BASE_URL}/zones",
        params={"name": dns_zone},
        headers=get_headers(api_key),
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        raise DyndnsError(
            f"Error retrieving zone: {response.status_code} {response.text}"
        )
    zones: list[dict] = response.json().get("zones", [])
    if not zones:
        raise DyndnsError(f"Zone '{dns_zone}' not found. Check DNS_ZONE in .env.")
    return str(zones[0]["id"])


def get_rrsets(api_key: str, zone_id: str) -> list[dict]:
    response = requests.get(
        f"{BASE_URL}/zones/{zone_id}/rrsets",
        headers=get_headers(api_key),
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code != 200:
        raise DyndnsError(
            f"Error retrieving RRsets: {response.status_code} {response.text}"
        )
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
        timeout=REQUEST_TIMEOUT,
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
        timeout=REQUEST_TIMEOUT,
    )
    if response.status_code not in (200, 201):
        print(f"{name}: Failed to create RRset: {response.status_code} {response.text}")
        return False
    return True


def update_record(
    config: Config, zone_id: str, name: str, current_ip: str, external_ip: str
) -> None:
    if current_ip == external_ip:
        print(f"{name}: IP unchanged ({external_ip}). No update necessary.")
        return

    if current_ip:
        print(f"Updating IP for {name}: {current_ip} → {external_ip}")
        if not delete_rrset(config.api_key, zone_id, name):
            return
    else:
        print(f"Creating new A record for {name}...")

    create_rrset(config.api_key, zone_id, name, external_ip)


def update_all_records(config: Config) -> None:
    external_ip = get_external_ip()
    zone_id = get_zone_id(config.api_key, config.dns_zone)
    rrsets = get_rrsets(config.api_key, zone_id)

    for name in config.dyndns_names:
        update_record(config, zone_id, name, find_rrset(rrsets, name), external_ip)


def run_once(config: Config) -> bool:
    """Runs one update; network and API errors become a single log line."""
    try:
        update_all_records(config)
    except requests.RequestException as error:
        print(f"Network error: {error}")
        return False
    except DyndnsError as error:
        print(error)
        return False
    return True


def main() -> None:
    args = parse_args()
    try:
        config = load_config()
    except DyndnsError as error:
        print(error)
        sys.exit(1)

    if args.interval is None:
        sys.exit(0 if run_once(config) else 1)

    while True:
        run_once(config)
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
