#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.client
import ipaddress
import time
import urllib.parse
import urllib.request
from pathlib import Path


OPENCCK_SITES = (
    "youtube.com",
    "aistudio.google.com",
    "chatgpt.com",
    "claude.ai",
    "telegram.org",
    "whatsapp.com",
    "grok.com",
    "instagram.com",
)
DEFAULT_OUTPUT_DIR = Path("dist")


def opencck_url(host: str, data_type: str, sites: tuple[str, ...] = ()) -> str:
    query = [("format", "text"), ("data", data_type)]
    if data_type == "domains":
        query.append(("wildcard", "1"))
    query.extend(("site", site) for site in sites)
    return f"https://{host}/?{urllib.parse.urlencode(query)}"


SOURCES = {
    "russia-direct": {
        "name": "OpenCCK Russia Direct",
        "host": "russia.iplist.opencck.org",
        "sites": (),
    },
    "selected-proxy": {
        "name": "OpenCCK Selected Services Proxy",
        "host": "iplist.opencck.org",
        "sites": OPENCCK_SITES,
    },
}
DATA_TYPES = ("domains", "cidr4", "cidr6")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Shadowrocket RULE-SET files from OpenCCK lists."
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def fetch_text(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "VPN-list-generator/1.0",
            "Accept-Encoding": "identity",
            "Connection": "close",
        },
    )

    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                encoding = response.headers.get_content_charset() or "utf-8"
                chunks = []
                while True:
                    chunk = response.read(1024 * 64)
                    if not chunk:
                        break
                    chunks.append(chunk)
                return b"".join(chunks).decode(encoding, errors="replace")
        except (TimeoutError, OSError, http.client.IncompleteRead) as error:
            last_error = error
            if attempt == 3:
                break
            time.sleep(attempt * 2)

    raise RuntimeError(f"Failed to fetch {url}") from last_error


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


def build_rules(data_type: str, text: str) -> list[str]:
    if data_type == "domains":
        return build_domain_rules(text)
    return build_ip_rules(text)


def write_rules(
    path: Path,
    name: str,
    sources: list[str],
    rules: list[str],
) -> None:
    source_lines = [f"# SOURCE: {source}" for source in sources]
    content = "\n".join(
        [
            f"# NAME: {name}",
            "# FORMAT: Shadowrocket RULE-SET",
            *source_lines,
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

    for slug, source in SOURCES.items():
        combined_rules: list[str] = []
        combined_urls: list[str] = []

        for data_type in DATA_TYPES:
            url = opencck_url(source["host"], data_type, source["sites"])
            print(f"Fetching {slug} {data_type}: {url}")
            text = fetch_text(url)
            rules = build_rules(data_type, text)

            part_path = output_dir / f"opencck-{slug}-{data_type}.list"
            part_name = f"{source['name']} {data_type}"
            write_rules(part_path, part_name, [url], rules)
            print(f"Wrote {part_path} ({len(rules)} rules)")

            combined_rules.extend(rules)
            combined_urls.append(url)

        combined_path = output_dir / f"opencck-{slug}.list"
        write_rules(combined_path, source["name"], combined_urls, combined_rules)
        print(f"Wrote {combined_path} ({len(combined_rules)} rules)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
