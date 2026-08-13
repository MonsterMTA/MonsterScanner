# Cloudflare IP & Domain Scanner

A Python tool to scan Cloudflare IPs and domains, measuring TCP latency and packet loss from Iran.

## Features

- **Random IP Sweep** — Scans random IPs from Cloudflare's subnet ranges
- **Neighbor Scanning** — When a valid IP is found, scans neighboring IPs in the same /24 block
- **Domain Testing** — Tests real-world domains behind Cloudflare
- **SNI Spoofing Scan** — Tests SNI domains (hcaptcha, cdns, etc.) to find low-latency endpoints
- **TCP 3-Way Handshake** — All pings use actual TCP SYN/ACK for accurate latency measurement
- **Packet Loss Tracking** — Shows loss percentage and min/max RTT jitter
- **Colo Cache** — Persists colo data between runs to reduce API calls
- **Multi-threaded** — Fast concurrent scanning with configurable thread count

## Requirements

- Python 3.11+
- No external dependencies (uses only standard library)

## Installation

```bash
git clone https://github.com/MonsterMTA/CF-Scanner.git
cd CF-Scanner
# No pip install needed - uses only Python standard library
```

## Usage

### Basic Usage

```bash
python scanner.py
```

### Common Options

```bash
# Quick test (few IPs, few pings)
python scanner.py -n 100 -T 10 --ping-count 2

# Full scan with all features
python scanner.py -n 50000 -T 75 --ping-count 4

# Only IPs, no domains/SNI
python scanner.py -n 5000 --no-domain --no-sni-scan

# Only domains, no IP sweep
python scanner.py --no-neighbor --no-domain --no-sni-scan

# Limit SNI tests
python scanner.py --sni-limit 20

# Custom ports
python scanner.py -p 80,443

# Custom SNI list from file
python scanner.py --sni-list my_snis.txt
```

### CLI Arguments

| Flag | Description | Default |
|------|-------------|---------|
| `-t`, `--timeout` | TCP connect timeout (seconds) | `1.0` |
| `-T`, `--threads` | Concurrent threads | `75` |
| `-n`, `--total` | Random IPs to sweep | `50000` |
| `-b`, `--neighbor` | Global neighbor limit | `200` |
| `-p`, `--ports` | Comma-separated ports | `80` |
| `--subnets-url` | Cloudflare subnets URL | (remote) |
| `--domains-url` | Domain list URL | (remote) |
| `--sni-url` | SNI domains URL | (remote) |
| `--sni-list` | Local SNI domains file | - |
| `--ping-count` | TCP handshakes per probe | `4` |
| `--sni-limit` | Max SNI domains to test | all |
| `--output-dir` | Results output directory | `./results` |
| `--cache-file` | Colo cache file path | `./colo_cache.json` |
| `--no-neighbor` | Skip neighbor scanning | - |
| `--no-domain` | Skip domain scanning | - |
| `--no-sni-scan` | Skip SNI domain scan | - |

## Data Sources

### Domain Lists

Domains are fetched from:
- **Main domains**: https://github.com/MonsterMTA/MonsterScanner/blob/main/cf-domains.txt (230 domains)
- **SNI domains**: https://github.com/MonsterMTA/MonsterScanner/blob/main/sni-domains.txt (64 domains)

### Cloudflare Subnets

Subnets from: https://github.com/ircfspace/cf-ip-ranges

## Output

### Results Format

Results are saved to `results/valid_ips_YYYY-MM-DD_HH-MM-SS.txt`:
```
# Valid Cloudflare IPs — 2026-08-13 18:10:01
# Format: IP:PORT
# ==================================================
104.16.10.5:80
172.67.20.3:80
```

### Console Output

```
🏆 TOP 20 — Sorted by TCP Ping
 1. 🌍 [DOMAIN] opencode.ai         | 172.65.90.22 |  50.5ms | loss:0/4 (0%) | 49-52ms | EWR
 2. 🌍 [SNI  ] hcaptcha.com          | 104.19.229.21 |  65.2ms | loss:0/4 (0%) | 63-68ms | GYD
 3. 🌍 [IP   ] 104.24.145.167        | 104.24.145.167 | 114.9ms | loss:0/4 (0%) | 113-117ms | FRA

📊 STATISTICS
  Subnets loaded:          4661
  Random IPs scanned:      20
  Valid random IPs found:  11
  Domains loaded:          230
  Valid domains found:     155
  SNI domains loaded:      64
  Valid SNI found:         30
  Total valid endpoints:   196
  Total packet losses:     14/784 (1.8%)
```

## How It Works

### Phase 1: Random IP Sweep
- Generates random IPs from Cloudflare's /8 ranges (104.16.0.0/12, 172.64.0.0/10)
- Performs TCP handshake pings to each IP
- Validates response via `/cdn-cgi/trace` endpoint

### Phase 2: Neighbor Scanning
- When a valid IP is found, scans neighboring IPs in the same /24 block
- Uses hop-based approach: scans one subnet at a time
- Global limit prevents excessive scanning

### Phase 3: Domain Testing
- Resolves domains to their Cloudflare IPs
- Performs TCP handshake pings
- Validates Cloudflare response

### Phase 4: SNI Spoofing
- Tests SNI domains (like hcaptcha.com, cdns, etc.)
- Resolves to Cloudflare IPs
- Useful for finding low-latency SNI endpoints

### Packet Loss Measurement
- Each probe performs N TCP handshakes (default: 4)
- Lost packets are counted when connection times out
- Shows loss percentage and min/max RTT jitter

## colo Cache

The scanner persists colo data to `colo_cache.json` between runs:
- First run: All lookups are HTTP requests
- Subsequent runs: Cache hits bypass HTTP calls
- Reduces latency and API load

## License

MIT License
