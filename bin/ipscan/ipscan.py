import json
import logging
import os
import ipaddress

from urllib.parse import urlparse
from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeoutError
)
from dns import resolver
from ipwhois import IPWhois

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)
_asn_cache = []

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
WHITELIST_PATH = os.path.join(
    SCRIPT_DIR, '../../',
    'external/russia-mobile-internet-whitelist/whitelist.txt'
)
OUTPUT_PATH = os.path.join(SCRIPT_DIR, '../../etc/ipscan/cidrs.json')


def _build_asn_cache():
    asn_ip_dir = os.path.join(SCRIPT_DIR, '../../external/asn-ip/as')
    as_dirs = [f.path for f in os.scandir(asn_ip_dir) if f.is_dir()]

    for as_dir in as_dirs:
        aggregated_file = os.path.join(as_dir, "aggregated.json")

        with open(aggregated_file, 'r', encoding='utf-8') as f:
            asn_data = json.load(f)

            for subnet in asn_data['subnets']['ipv4']:
                network = ipaddress.IPv4Network(subnet)

                _asn_cache.append({
                    'cidr': network,
                    'net_name': asn_data.get('handle', ''),
                    'country': '',
                    'asn': asn_data.get('asn', ''),
                    'asn_description': asn_data.get('description', ''),
                })


def resolve_domain_to_ips(domain):
    """
    Resolve a domain to its associated IP addresses.
    """
    logger.info("Resolving: %s", domain)
    ips = set()

    try:
        answers = resolver.resolve(domain, "A")
        for r in answers:
            ips.add(r.to_text())
    except Exception as e:
        logger.error("Failed to resolve %s. Error: %r", domain, e)
    return ips


def get_cidr_info_from_files(ip):
    """
    Get CIDR information for a specific IP address from files.
    """
    logger.info("Getting CIDR info: %s", ip)

    try:
        if not _asn_cache:
            _build_asn_cache()

        ip = ipaddress.ip_address(ip)

        for asn_data in _asn_cache:
            if ip in asn_data['cidr']:
                return {
                    "cidr": str(asn_data['cidr']),
                    "net_name": asn_data['net_name'],
                    'country': '',
                    "asn": str(asn_data['asn']),
                    "asn_description": asn_data['asn_description'],
                }
        logger.warning("No CIDR info for %s", str(ip))
    except Exception as e:
        logger.error("Failed to get CIDR info for %s. Error: %r", ip, e)
    return {}


def get_cidr_info_from_whois(ip):
    """
    Get CIDR information for a specific IP address via whois.
    """
    logger.info("Getting CIDR info: %s", ip)

    try:
        obj = IPWhois(ip)
        res = obj.lookup_rdap(depth=1)

        return {
            "cidr": res.get("network", {}).get("cidr"),
            "net_name": res.get("network", {}).get("name"),
            "country": res.get("network", {}).get("country"),
            "asn": res.get("asn"),
            "asn_description": res.get("asn_description"),
        }
    except Exception as e:
        logger.error("Failed to get CIDR info for %s. Error: %r", ip, e)
    return {}


def get_domain_info(domain):
    """
    Get information for a domain, including associated IPs and their CIDR 
    information.
    """
    ips = resolve_domain_to_ips(domain)
    result = {}

    if ips:
        for ip in ips:
            result[ip] = get_cidr_info_from_files(ip)

    return result


def collect_domains_with_browser(url, max_time=15000):
    """
    Use Playwright to open a URL and collect domains observed during navigation 
    requests.
    """
    domains = set()
    logger.info("Playwright: opening %s", url)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            def on_request(request):
                u = request.url
                method = request.method
                host = urlparse(u).hostname
                logger.info("Playwright request: %s %s", method, u)
                if host:
                    domains.add(host)

            page.on("request", on_request)

            page.set_extra_http_headers({
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
                    "application/signed-exchange;v=b3;q=0.9"
                ),
                "Accept-Encoding": "gzip, deflate, br",
                "Accept-Language": "en-US,en;q=0.9",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Sec-CH-UA": '"Chromium";v="125", "Not.A/Brand";v="24"',
                "Sec-CH-UA-Mobile": "?0",
                "Sec-CH-UA-Platform": '"Windows"',
            })

            try:
                page.goto(url, wait_until="networkidle", timeout=max_time)
            except PlaywrightTimeoutError as e:
                logger.warning("Playwright timeout for %s: %r", url, e)
            except Exception as e:
                logger.warning(
                    "Playwright error during goto for %s: %r", url, e
                )

            try:
                page.wait_for_timeout(2000)
            except Exception:
                pass
            finally:
                browser.close()

    except Exception as e:
        logger.warning("Playwright failed to start or run for %s: %r", url, e)

    logger.info("Playwright: %s -> %d unique domains", url, len(domains))
    return domains


def main():
    """Main function to process domains and update the CIDR information."""
    domains_cidrs = {}

    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
            domains_cidrs = json.load(f)

    with open(WHITELIST_PATH, 'r', encoding='utf-8') as f:
        whitelist = f.readlines()

    for domain in whitelist:
        domain = domain.strip()

        if domain in domains_cidrs and domains_cidrs[domain]:
            logger.info('Domain already processed and has info: %s', domain)
            continue

        try:
            domains_cidrs[domain] = get_domain_info(domain)

            requested_domains = collect_domains_with_browser(
                f'http://{domain}')

            for requested_domain in requested_domains:
                if requested_domain not in domains_cidrs:
                    domains_cidrs[requested_domain] = get_domain_info(
                        requested_domain)

            with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(domains_cidrs, f, indent=2)

        except Exception as e:
            logger.error('Failed to process domain %s: %r', domain, e)


if __name__ == '__main__':
    main()
