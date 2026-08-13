# MonsterScanner — Cloudflare IP & Domain Scanner

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A fast, multi-threaded Python tool to scan Cloudflare IPs and domains — measuring real TCP latency and packet loss from Iran.

ابزاری سریع و چندرشته‌ای پایتون برای اسکن IPها و دامنه‌های کلادفلر — اندازه‌گیری latency واقعی TCP و packet loss از ایران.

---

## 🚀 Quick Start / شروع سریع

```bash
# Clone / کلون
git clone https://github.com/MonsterMTA/MonsterScanner.git
cd MonsterScanner

# Run / اجرا
python scanner.py
```

---

## ✨ Features / ویژگی‌ها

| Feature | توضیح |
|---------|-------|
| **Random IP Sweep** | اسکن IP تصادفی از subnetهای کلادفلر |
| **Neighbor Scanning** | اسکن همسایه‌ها در /24 block |
| **Domain Testing** | تست 230+ دامنه واقعی |
| **SNI Spoofing** | تست 64+ دامنه SNI (hcaptcha, cdns, etc.) |
| **TCP 3-Way Handshake** | پینگ واقعی TCP SYN/ACK |
| **Packet Loss Tracking** | نمایش درصد لاس و jitter |
| **Colo Cache** | کش بین اجراها |
| **Multi-threaded** | اسکن موازی قابل تنظیم |

---

## 📋 Requirements / پیش‌نیازها

- Python 3.11+
- No external dependencies (standard library only)
- Network access to Cloudflare IPs

---

## 🛠️ Usage / نحوه استفاده

### Basic / اساسی

```bash
python scanner.py
```

### Common Examples / مثال‌های پرکاربرد

```bash
# Quick test / تست سریع
python scanner.py -n 100 -T 10 --ping-count 2

# Full scan / اسکن کامل
python scanner.py -n 50000 -T 75 --ping-count 4

# Only IPs / فقط IP
python scanner.py -n 5000 --no-domain --no-sni-scan

# Only domains / فقط دامنه
python scanner.py --no-neighbor --no-sni-scan

# Limit SNI / محدود کردن SNI
python scanner.py --sni-limit 20

# Custom ports / پورت دلخواه
python scanner.py -p 80,443

# Local SNI file / فایل SNI محلی
python scanner.py --sni-list my_snis.txt
```

### All Options / همه گزینه‌ها

| Flag | Description | پیش‌فرض |
|------|-------------|---------|
| `-t`, `--timeout` | TCP timeout (s) | `1.0` |
| `-T`, `--threads` | Thread count | `75` |
| `-n`, `--total` | IPs to sweep | `50000` |
| `-b`, `--neighbor` | Neighbor limit | `200` |
| `-p`, `--ports` | Ports (comma) | `80` |
| `--ping-count` | Pings per probe | `4` |
| `--sni-limit` | Max SNI domains | all |
| `--no-neighbor` | Skip neighbor | - |
| `--no-domain` | Skip domains | - |
| `--no-sni-scan` | Skip SNI | - |
| `--sni-url` | Custom SNI URL | (remote) |
| `--sni-list` | Local SNI file | - |
| `--output-dir` | Output directory | `./results` |
| `--cache-file` | Cache file | `./colo_cache.json` |

---

## 📊 Output Examples / نمونه خروجی

```
⚙️  timeout=1.0s  threads=8  total=20  ports=[80]  neighbor=200  ping_count=2
📁 Output : results/valid_ips_2026-08-13_18-16-00.txt
💾 Cache  : colo_cache.json

🌐 Fetching remote data...
✅ Loaded 4661 subnets
✅ Loaded 230 domains
✅ Loaded 64 SNI domains

📡 Scanning 20 random IPs...
✅ IP scan: 11 valid in 4.1s

🌐 Testing 230 domains...
✅ Domain scan: 155 valid in 32.3s

🔐 SNI spoofing scan: 64 domains...
✅ SNI scan: 30 valid in 2.1s

===========================================================================
🏆 TOP 20 — Sorted by TCP Ping
===========================================================================
 1. 🌍 [DOMAIN] opencode.ai         | 172.65.90.22 |  50.5ms | loss:0/2 (0%) | 49-52ms | EWR
 2. 🌍 [SNI  ] hcaptcha.com          | 104.19.229.21 |  65.2ms | loss:0/2 (0%) | 63-68ms | GYD
 3. 🌍 [IP   ] 104.24.145.167        | 104.24.145.167 | 114.9ms | loss:0/2 (0%) | 113-117ms | FRA

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

---

## 📁 Files / فایل‌ها

| File | توضیح |
|------|-------|
| `scanner.py` | Main scanner script |
| `colo_cache.json` | Cached colo data |
| `results/` | Output directory |

---

## 🔗 Data Sources / منابع داده

- **Cloudflare Subnets**: [ircfspace/cf-ip-ranges](https://github.com/ircfspace/cf-ip-ranges)
- **Domain List**: [cf-domains.txt](https://github.com/MonsterMTA/MonsterScanner/blob/main/cf-domains.txt) (230 domains)
- **SNI List**: [sni-domains.txt](https://github.com/MonsterMTA/MonsterScanner/blob/main/sni-domains.txt) (64 domains)

---

## 🙏 Acknowledgments / تشکر و قدردانی

- **ircfspace** — For maintaining and providing the Cloudflare subnet list: https://github.com/ircfspace/cf-ip-ranges
- **hossein-mohseni** — For the CF-Web domain list

---

## 📝 License / لایسنس

MIT License

---

© 2026 MonsterMTA. All rights reserved.
