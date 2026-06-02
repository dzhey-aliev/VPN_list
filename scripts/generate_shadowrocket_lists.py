#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ipaddress
import urllib.request
from pathlib import Path


DEFAULT_DOMAINS_URL = "https://community.antifilter.download/list/domains.lst"
DEFAULT_IP_URL = "https://community.antifilter.download/list/community.lst"
DEFAULT_OUTPUT_DIR = Path("dist")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Shadowrocket RULE-SET files from Antifilter lists."
    )
    parser.add_argument("--domains-url", default=DEFAULT_DOMAINS_URL)
    parser.add_argument("--ip-url", default=DEFAULT_IP_URL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "VPN-list-generator/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        encoding = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(encoding, errors="replace")


def iter_clean_lines(text: str):
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        yield line


def normalize_domain(line: str) -> str:
    domain = line.split()[0].strip().strip(".").lower()
    if domain.startswith("*."):
        domain = domain[2:]
    return domain


def build_domain_rules(text: str) -> list[str]:
    domains = {
        domain
        for domain in (normalize_domain(line) for line in iter_clean_lines(text))
        if domain
    }
    return [f"DOMAIN-SUFFIX,{domain}" for domain in sorted(domains)]


def parse_network(line: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
    value = line.split()[0].strip()
    return ipaddress.ip_network(value, strict=False)


def build_ip_rules(text: str) -> list[str]:
    networks = {parse_network(line) for line in iter_clean_lines(text)}
    sorted_networks = sorted(
        networks,
        key=lambda network: (
            network.version,
            int(network.network_address),
            network.prefixlen,
        ),
    )

    rules = []
    for network in sorted_networks:
        rule_type = "IP-CIDR6" if network.version == 6 else "IP-CIDR"
        rules.append(f"{rule_type},{network},no-resolve")
    return rules


def write_rules(path: Path, source_url: str, rules: list[str]) -> None:
    content = "\n".join(
        [
            "# NAME: Antifilter Community",
            "# FORMAT: Shadowrocket RULE-SET",
            f"# SOURCE: {source_url}",
            f"# TOTAL: {len(rules)}",
            *rules,
            "",
        ]
    )
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content, encoding="utf-8", newline="\n")
    tmp_path.replace(path)


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching domains: {args.domains_url}")
    domains_text = fetch_text(args.domains_url)
    domain_rules = build_domain_rules(domains_text)

    print(f"Fetching IP networks: {args.ip_url}")
    ip_text = fetch_text(args.ip_url)
    ip_rules = build_ip_rules(ip_text)

    domains_path = output_dir / "antifilter-domains.list"
    ip_path = output_dir / "antifilter-community-ip.list"

    write_rules(domains_path, args.domains_url, domain_rules)
    write_rules(ip_path, args.ip_url, ip_rules)

    print(f"Wrote {domains_path} ({len(domain_rules)} rules)")
    print(f"Wrote {ip_path} ({len(ip_rules)} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
