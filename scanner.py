import sys as _sys
import io as _io
import os
import ipaddress
import socket
import urllib.request
import json
import time
import random
import concurrent.futures
import threading
import argparse
import re
from datetime import datetime

if _sys.platform == "win32":
    _enc = os.environ.get("PYTHONIOENCODING", "utf-8")
    for _name in ("stdout", "stderr"):
        _stream = getattr(_sys, _name)
        if hasattr(_stream, "buffer") and getattr(_stream, "encoding", None) != _enc:
            setattr(_sys, _name, _io.TextIOWrapper(
                _stream.buffer, encoding=_enc, errors="replace", line_buffering=True))

DEFAULT_TIMEOUT     = 1.0
DEFAULT_THREADS     = 75
DEFAULT_TOTAL       = 50000
DEFAULT_NEIGHBOR    = 200
DEFAULT_PORTS       = [80]
DEFAULT_PING_COUNT  = 4

SUBNETS_URL = "https://raw.githubusercontent.com/ircfspace/cf-ip-ranges/main/export.ipv4"
DOMAINS_URL = "https://raw.githubusercontent.com/MonsterMTA/MonsterScanner/main/sources/cf-domains.txt"
SNI_URL     = "https://raw.githubusercontent.com/MonsterMTA/MonsterScanner/main/sources/sni-domains.txt"

colo_cache: dict   = {}
cache_hits: int    = 0
cache_misses: int  = 0
file_lock = threading.Lock()
scan_lock = threading.Lock()
_cfg: argparse.Namespace | None = None


def cfg() -> argparse.Namespace:
    assert _cfg is not None
    return _cfg


def load_cache(path: str) -> None:
    global colo_cache
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                colo_cache = json.load(f)
            print(f"💾 Loaded {len(colo_cache)} cached colo entries from {path}")
        except Exception:
            colo_cache = {}

def save_cache(path: str) -> None:
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(colo_cache, f, indent=2)
        os.replace(tmp, path)
    except Exception as e:
        print(f"⚠️  Failed to save cache: {e}")

def save_result(ip: str, port: int, path: str) -> None:
    with file_lock:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{ip}:{port}\n")
            f.flush()

def fetch_subnets(url: str) -> list[str]:
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            lines = [ln.strip() for ln in r.read().decode("utf-8").splitlines() if ln.strip()]
        print(f"✅ Loaded {len(lines)} subnets from {url}")
        return lines
    except Exception as e:
        print(f"❌ Failed to fetch subnets: {e}")
        return ["104.21.0.0/24", "172.67.0.0/24"]

def fetch_domains(url: str) -> list[dict]:
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            content = r.read().decode("utf-8")
        if content.strip().startswith("{"):
            data = json.loads(content)
            domains = data.get("data", [])
        else:
            lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
            domains = [{"domain": ln, "ipv4": ""} for ln in lines]
        print(f"✅ Loaded {len(domains)} domains from {url}")
        return domains
    except Exception as e:
        print(f"❌ Failed to fetch domains: {e}")
        return []

def fetch_sni_domains(url: str) -> list[str]:
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            remote = [ln.strip() for ln in r.read().decode("utf-8").splitlines() if ln.strip()]
        print(f"✅ Loaded {len(remote)} SNI domains from {url}")
        return remote
    except Exception:
        return []

def tcp_handshake_ping(ip: str, port: int, count: int = 4,
                       timeout: float = 1.0) -> tuple[list[float], int]:
    rtt: list[float] = []
    lost = 0
    for _ in range(count):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            start = time.time()
            s.connect((ip, port))
            elapsed = (time.time() - start) * 1000
            rtt.append(round(elapsed, 1))
            s.close()
        except Exception:
            lost += 1
    return rtt, lost

def get_colo(ip: str) -> str:
    global cache_hits, cache_misses
    if ip in colo_cache:
        cache_hits += 1
        return colo_cache[ip]
    cache_misses += 1
    try:
        req = urllib.request.Request(f"http://{ip}/cdn-cgi/trace",
                                     headers={"Host": "cloudflare.com"})
        with urllib.request.urlopen(req, timeout=2.0) as r:
            for line in r.read().decode("utf-8").split("\n"):
                if line.startswith("colo="):
                    colo = line.split("=", 1)[1].strip()
                    colo_cache[ip] = colo
                    return colo
    except Exception:
        pass
    colo_cache[ip] = "UNKNOWN"
    return "UNKNOWN"

def ip_to_int(ip: str) -> int:
    return int(ipaddress.IPv4Address(ip))

def int_to_ip(n: int) -> str:
    return str(ipaddress.IPv4Address(n))

def subnet_of(ip: str) -> str:
    addr = ipaddress.IPv4Address(ip)
    net_mask = 0xFFFFFFFF << (32 - 24)
    net_start = int(addr) & net_mask
    return str(ipaddress.IPv4Network(f"{int_to_ip(net_start)}/24", strict=False))

def check_ip(ip: str) -> tuple | None:
    c = cfg()
    for port in c.ports:
        rtt_vals, lost = tcp_handshake_ping(ip, port, count=c.ping_count, timeout=c.timeout)
        if rtt_vals:
            avg = round(sum(rtt_vals) / len(rtt_vals), 1)
            colo = get_colo(ip)
            if colo != "UNKNOWN":
                save_result(ip, port, c.output_file)
                return (ip, avg, colo, port, rtt_vals, lost)
    return None

def test_domain(entry: dict) -> tuple | None:
    c = cfg()
    domain = entry.get("domain")
    ip = entry.get("ipv4")
    if not ip:
        try:
            ip = socket.gethostbyname(domain)
        except Exception:
            return None
    for port in c.ports:
        rtt_vals, lost = tcp_handshake_ping(ip, port, count=c.ping_count, timeout=c.timeout)
        if rtt_vals:
            colo = get_colo(ip)
            if colo != "UNKNOWN":
                save_result(ip, port, c.output_file)
                avg = round(sum(rtt_vals) / len(rtt_vals), 1)
                return (domain, ip, avg, colo, port, rtt_vals, lost)
    return None

def test_sni_domain(domain: str) -> tuple | None:
    c = cfg()
    try:
        ip = socket.gethostbyname(domain)
    except Exception:
        return None
    for port in c.ports:
        rtt_vals, lost = tcp_handshake_ping(ip, port, count=c.ping_count, timeout=c.timeout)
        if rtt_vals:
            colo = get_colo(ip)
            if colo != "UNKNOWN":
                save_result(ip, port, c.output_file)
                avg = round(sum(rtt_vals) / len(rtt_vals), 1)
                return (domain, ip, avg, colo, port, rtt_vals, lost)
    return None

def generate_random_ips(subnets: list[str], count: int) -> list[str]:
    networks = [ipaddress.ip_network(s, strict=False) for s in subnets]
    weights  = [net.num_addresses for net in networks]
    ips = set()
    while len(ips) < count:
        net = random.choices(networks, weights=weights)[0]
        lo, hi = int(net.network_address) + 1, int(net.broadcast_address) - 1
        if lo <= hi:
            ips.add(str(ipaddress.ip_address(random.randint(lo, hi))))
    return list(ips)

def is_ip_addr(name: str) -> bool:
    return bool(re.match(r'^\d{1,3}(\.\d{1,3}){3}$', name))

def main() -> None:
    global cache_hits, cache_misses

    ap = argparse.ArgumentParser(
        description="🔍 Cloudflare IP & Domain Scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scanner.py
  python scanner.py -n 20000 -T 50 --ports 80,443
  python scanner.py -n 5000 --ping-count 10
  python scanner.py -n 5000 --no-sni-scan
  python scanner.py --sni-list my_snis.txt
        """)

    ap.add_argument("-t", "--timeout",     type=float, default=DEFAULT_TIMEOUT,
                    help="TCP connect timeout (s)")
    ap.add_argument("-T", "--threads",     type=int,   default=DEFAULT_THREADS,
                    help="Concurrent threads")
    ap.add_argument("-n", "--total",       type=int,   default=DEFAULT_TOTAL,
                    help="Random IPs to sweep")
    ap.add_argument("-b", "--neighbor",    type=int,   default=DEFAULT_NEIGHBOR,
                    help="Global neighbor limit (min 1000)")
    ap.add_argument("-p", "--ports",       type=str,   default="80",
                    help="Comma-separated ports")
    ap.add_argument("--subnets-url",       type=str,   default=SUBNETS_URL)
    ap.add_argument("--domains-url",       type=str,   default=DOMAINS_URL)
    ap.add_argument("--output-dir",        type=str,   default=None)
    ap.add_argument("--cache-file",        type=str,   default=None)
    ap.add_argument("--no-neighbor",       action="store_true")
    ap.add_argument("--no-domain",         action="store_true")
    ap.add_argument("--no-sni-scan",       action="store_true",
                    help="Skip SNI domain scan")
    ap.add_argument("--sni-url",           type=str,   default=SNI_URL,
                    help="URL to fetch additional SNI domains")
    ap.add_argument("--sni-list",          type=str,   default=None,
                    help="Local file with one SNI domain per line")
    ap.add_argument("--ping-count",        type=int,   default=DEFAULT_PING_COUNT,
                    help=f"TCP handshakes per probe (default: {DEFAULT_PING_COUNT})")
    ap.add_argument("--sni-limit",         type=int,   default=None,
                    help="Max SNI domains to test (default: all)")

    args = ap.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = args.output_dir  or os.path.join(script_dir, "results")
    cache_file = args.cache_file  or os.path.join(script_dir, "colo_cache.json")
    ports      = [int(p.strip()) for p in args.ports.split(",") if p.strip()]
    ts         = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = os.path.join(output_dir, f"valid_ips_{ts}.txt")

    global _cfg
    _cfg = argparse.Namespace(
        timeout=args.timeout, threads=args.threads, total=args.total,
        neighbor=args.neighbor, ports=ports, ping_count=args.ping_count,
        subnets_url=args.subnets_url, domains_url=args.domains_url,
        output_file=output_file, cache_file=cache_file,
        output_dir=output_dir,
        skip_neighbor=args.no_neighbor, skip_domain=args.no_domain,
        skip_sni=args.no_sni_scan,
    )

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(script_dir, "results"), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"# Valid Cloudflare IPs — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# Format: IP:PORT\n")
        f.write("# " + "=" * 50 + "\n")

    print(f"⚙️  timeout={args.timeout}s  threads={args.threads}  total={args.total}"
          f"  ports={ports}  neighbor={args.neighbor}  ping_count={args.ping_count}"
          f"{'  [NEIGHBOR SKIP]' if args.no_neighbor else ''}"
          f"{'  [DOMAIN SKIP]' if args.no_domain else ''}"
          f"{'  [SNI SKIP]' if args.no_sni_scan else ''}")
    print(f"📁 Output : {output_file}")
    print(f"💾 Cache  : {cache_file}")
    print()

    print("🌐 Fetching remote data...")
    subnets = fetch_subnets(args.subnets_url)
    domains = fetch_domains(args.domains_url) if not args.no_domain else []
    sni_remote = fetch_sni_domains(args.sni_url) if not args.no_sni_scan else []

    sni_domains = sni_remote[:args.sni_limit] if args.sni_limit else sni_remote
    if not subnets:
        print("❌ No subnets loaded — exiting.")
        return

    load_cache(cache_file)

    print(f"\n📡 Scanning {args.total} random IPs from {len(subnets)} subnets...")
    ip_list   = generate_random_ips(subnets, args.total)
    ip_results: list = []
    found_valid: list = []
    t0 = time.time()
    processed = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as ex:
        futs = {ex.submit(check_ip, ip): ip for ip in ip_list}
        for fut in concurrent.futures.as_completed(futs):
            processed += 1
            res = fut.result()
            if res:
                ip_results.append(res)
                with scan_lock:
                    found_valid.append(res[0])
            if processed % 100 == 0:
                print(f"   IP: {processed}/{args.total} — {len(ip_results)} valid — {time.time()-t0:.0f}s")

    print(f"✅ IP scan: {len(ip_results)} valid in {time.time()-t0:.1f}s")

    neighbor_results: list = []
    total_nb_scanned = 0
    if not args.no_neighbor and found_valid:
        print(f"\n🔍 Found {len(found_valid)} valid IPs — scanning neighbors...")
        global_limit = max(args.neighbor, 1000)
        neighbor_seen: set[str] = set(found_valid)
        scanned = 0
        skipped_subnets: set[str] = set()

        subnet_order: list[str] = []
        for ip_addr in found_valid:
            net = subnet_of(ip_addr)
            if net not in skipped_subnets and net not in subnet_order:
                subnet_order.append(net)

        print(f"   → {len(subnet_order)} unique /24 blocks  |  global limit: {global_limit} IPs")

        nb_t0 = time.time()
        skipped_count = 0
        sidx = 0

        while scanned < global_limit and sidx < len(subnet_order):
            net = ipaddress.IPv4Network(subnet_order[sidx], strict=False)
            sidx += 1
            candidates = [str(h) for h in net.hosts()
                          if str(h) not in neighbor_seen]
            batch = candidates[: (global_limit - scanned)]
            if not batch:
                continue

            print(f"   📍 Subnet {sidx}/{len(subnet_order)}: {net} "
                  f"({len(batch)} new  |  {scanned}/{global_limit} global)")

            with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as ex:
                futs = {ex.submit(check_ip, ip): ip for ip in batch}
                for fut in concurrent.futures.as_completed(futs):
                    ip_addr = futs[fut]
                    scanned += 1
                    try:
                        res = fut.result()
                    except Exception:
                        skipped_subnets.add(str(net))
                        skipped_count += 1
                        print(f"   ⏭️  Subnet {net} skipped")
                        for f2 in futs:
                            if f2 != fut:
                                f2.cancel()
                        break
                    if res:
                        neighbor_results.append(res)
                        with scan_lock:
                            found_valid.append(res[0])
                    if scanned % 100 == 0:
                        print(f"      global: {scanned}/{global_limit} — "
                              f"{len(neighbor_results)} valid — {time.time()-nb_t0:.0f}s")

        total_nb_scanned = scanned
        print(f"✅ Neighbor scan: {len(neighbor_results)} valid in "
              f"{time.time()-nb_t0:.1f}s ({skipped_count} subnets skipped)")

    domain_results: list = []
    if domains:
        print(f"\n🌐 Testing {len(domains)} domains "
              f"(TCP 3-way handshake × {args.ping_count} pings each)...")
        d0 = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(args.threads, len(domains))) as ex:
            futs = {ex.submit(test_domain, d): d for d in domains}
            for fut in concurrent.futures.as_completed(futs):
                res = fut.result()
                if res:
                    domain_results.append(res)
        print(f"✅ Domain scan: {len(domain_results)} valid in {time.time()-d0:.1f}s")
    elif not args.no_domain:
        print("ℹ️  No domains to test.\n")

    sni_results: list = []
    if sni_domains:
        print(f"\n🔐 SNI spoofing scan: {len(sni_domains)} domains "
              f"(TCP 3-way handshake × {args.ping_count} pings each)...")
        s0 = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(args.threads, len(sni_domains))) as ex:
            futs = {ex.submit(test_sni_domain, d): d for d in sni_domains}
            for fut in concurrent.futures.as_completed(futs):
                res = fut.result()
                if res:
                    sni_results.append(res)
        print(f"✅ SNI scan: {len(sni_results)} valid in {time.time()-s0:.1f}s")
    elif not args.no_sni_scan:
        print("ℹ️  No SNI domains to test.\n")

    save_cache(cache_file)

    ip_only = [(r[0], r[0], r[1], r[2], r[3], r[4], r[5]) for r in ip_results]
    domain_only = domain_results
    sni_only = sni_results

    ip_only.sort(key=lambda x: x[2])
    domain_only.sort(key=lambda x: x[2])
    sni_only.sort(key=lambda x: x[2])

    all_results = ip_only + domain_only + sni_only
    all_results.sort(key=lambda x: x[2])

    print("\n" + "=" * 75)
    print("🏆 TOP 20 — Sorted by TCP Ping")
    print("=" * 75)
    for i, res in enumerate(all_results[:20], 1):
        flag = "🇹🇷" if res[3] == "IST" else "🌍"
        name, ip, ping, colo, port, rtts, lost = res
        loss_pct = lost / args.ping_count * 100
        min_r = min(rtts); max_r = max(rtts)
        if is_ip_addr(name):
            tag = "IP"
        elif name in sni_domains or any(s in name for s in ["hcaptcha", "jsdelivr", "datatables", "stripe", "github", "googleapis", "gstatic", "imgur", "stackoverflow", "reddit", "steam", "shopify"]):
            tag = "SNI"
        else:
            tag = "DOMAIN"
        print(f"{i:2}. {flag} [{tag:5}] {name:25} | {ip:15} | {ping:5}ms "
              f"| loss:{lost}/{args.ping_count} ({loss_pct:.0f}%) | {min_r:.0f}-{max_r:.0f}ms | {colo}")

    if domain_only:
        print("\n" + "=" * 75 + "\n🌐 TOP DOMAINS\n" + "=" * 75)
        for name, ip, ping, colo, port, rtts, lost in domain_only[:10]:
            flag = "🇹🇷" if colo == "IST" else "🌍"
            loss_pct = lost / args.ping_count * 100
            min_r = min(rtts); max_r = max(rtts)
            print(f"  {flag} {name:30} | {ip:15} | {ping:5}ms "
                  f"| loss:{lost}/{args.ping_count} ({loss_pct:.0f}%) | {min_r:.0f}-{max_r:.0f}ms | {colo}")

    if sni_only:
        print("\n" + "=" * 75 + "\n🔐 TOP SNI\n" + "=" * 75)
        for name, ip, ping, colo, port, rtts, lost in sni_only[:10]:
            flag = "🇹🇷" if colo == "IST" else "🌍"
            loss_pct = lost / args.ping_count * 100
            min_r = min(rtts); max_r = max(rtts)
            print(f"  {flag} {name:30} | {ip:15} | {ping:5}ms "
                  f"| loss:{lost}/{args.ping_count} ({loss_pct:.0f}%) | {min_r:.0f}-{max_r:.0f}ms | {colo}")

    if ip_only:
        print("\n" + "=" * 75 + "\n🖥️  TOP IPs\n" + "=" * 75)
        for name, ip, ping, colo, port, rtts, lost in ip_only[:10]:
            flag = "🇹🇷" if colo == "IST" else "🌍"
            print(f"  {flag} {ip:15} | {port} | {ping}ms | {colo}")

    print("\n" + "=" * 75 + "\n📊 STATISTICS\n" + "=" * 75)
    print(f"  Subnets loaded:          {len(subnets)}")
    print(f"  Random IPs scanned:      {args.total}")
    print(f"  Neighbor IPs scanned:    {total_nb_scanned}")
    print(f"  Valid random IPs found:  {len(ip_only)}")
    print(f"  Valid neighbor IPs:      {len(neighbor_results)}")
    print(f"  Domains loaded:          {len(domains)}")
    print(f"  Valid domains found:     {len(domain_only)}")
    print(f"  SNI domains loaded:      {len(sni_domains)}")
    print(f"  Valid SNI found:         {len(sni_only)}")
    print(f"  Total valid endpoints:   {len(all_results)}")

    total_loss = sum(r[6] for r in all_results if len(r) == 7)
    total_pings = len([r for r in all_results if len(r) == 7]) * args.ping_count
    if total_pings:
        print(f"  Total packet losses:     {total_loss}/{total_pings} "
              f"({total_loss/total_pings*100:.1f}%)")

    if cache_hits + cache_misses:
        print(f"  Cache hit rate:          "
              f"{cache_hits/(cache_hits+cache_misses)*100:.1f}% "
              f"({cache_hits} hits / {cache_misses} misses)")
    print(f"\n📁 Results: {output_file}")
    print(f"💾 Cache saved to: {cache_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Stopped.")
        if _cfg is not None:
            save_cache(_cfg.cache_file)