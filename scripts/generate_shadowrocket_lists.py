#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ipaddress
import urllib.request
from pathlib import Path


DEFAULT_DIRECT_URL = "https://russia.iplist.opencck.org/?format=text&data=cidr4"
DEFAULT_PROXY_URL = (
    "https://iplist.opencck.org/?format=text&data=cidr4"
    "&site=youtube.com"
    "&site=aistudio.google.com"
    "&site=chatgpt.com"
    "&site=claude.ai"
    "&site=telegram.org"
    "&site=whatsapp.com"
    "&site=grok.com"
    "&site=instagram.com"
)
DEFAULT_OUTPUT_DIR = Path("dist")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Shadowrocket IP-only RULE-SET files from OpenCCK lists."
    )
    parser.add_argument("--direct-url", default=DEFAULT_DIRECT_URL)
    parser.add_argument("--proxy-url", default=DEFAULT_PROXY_URL)
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


def parse_network(line: str) -> ipaddress.IPv4Network | ipaddress.IPv6Network:
    value = line.split()[0].strip()
    return ipaddress.ip_network(value, strict=False)


def build_ip_rules(text: str) -> list[str]:
    networks = {parse_network(line) for line in iter_clean_lines(text)}
    collapsed_networks = ipaddress.collapse_addresses(networks)
    sorted_networks = sorted(
        collapsed_networks,
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


def write_rules(path: Path, name: str, source_url: str, rules: list[str]) -> None:
    content = "\n".join(
        [
            f"# NAME: {name}",
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


def remove_legacy_files(output_dir: Path) -> None:
    for filename in (
        "antifilter-domains.list",
        "antifilter-community-ip.list",
    ):
        path = output_dir / filename
        if path.exists():
            path.unlink()


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    remove_legacy_files(output_dir)

    print(f"Fetching proxy IP networks: {args.proxy_url}")
    proxy_text = fetch_text(args.proxy_url)
    proxy_rules = build_ip_rules(proxy_text)

    print(f"Fetching direct IP networks: {args.direct_url}")
    direct_text = fetch_text(args.direct_url)
    direct_rules = build_ip_rules(direct_text)

    proxy_path = output_dir / "opencck-selected-proxy.list"
    direct_path = output_dir / "opencck-russia-direct.list"

    write_rules(proxy_path, "OpenCCK Selected Services Proxy", args.proxy_url, proxy_rules)
    write_rules(direct_path, "OpenCCK Russia Direct", args.direct_url, direct_rules)

    print(f"Wrote {proxy_path} ({len(proxy_rules)} rules)")
    print(f"Wrote {direct_path} ({len(direct_rules)} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
