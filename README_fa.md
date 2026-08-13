# MonsterScanner — اسکنر IP و دامنه کلادفلر

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ابزاری سریع و چندرشته‌ای پایتون برای اسکن IPها و دامنه‌های کلادفلر — اندازه‌گیری latency واقعی TCP و packet loss از ایران.

---

## 🚀 شروع سریع

```bash
# Clone / کلون
git clone https://github.com/MonsterMTA/MonsterScanner.git
cd MonsterScanner

# Run / اجرا
python scanner.py
```

---

## ✨ ویژگی‌ها

| ویژگی | توضیح |
|-------|-------|
| **اسکن IP تصادفی** | اسکن IP تصادفی از subnetهای کلادفلر |
| **اسکن همسایه** | اسکن همسایه‌ها در /24 block |
| **تست دامنه** | تست 230+ دامنه واقعی |
| **SNI Spoofing** | تست 64+ دامنه SNI (hcaptcha, cdns, etc.) |
| **TCP 3-Way Handshake** | پینگ واقعی TCP SYN/ACK |
| **Packet Loss Tracking** | نمایش درصد لاس و jitter |
| **Colo Cache** | کش بین اجراها |
| **چند Threads** | اسکن موازی قابل تنظیم |

---

## 📋 پیش‌نیازها

- Python 3.11+
- بدون وابستگی خارجی (فقط کتابخانه استاندارد)
- دسترسی شبکه به IPهای کلادفلر

---

## 🛠️ نحوه استفاده

### اساسی

```bash
python scanner.py
```

### مثال‌های پرکاربرد

```bash
# تست سریع
python scanner.py -n 100 -T 10 --ping-count 2

# اسکن کامل
python scanner.py -n 50000 -T 75 --ping-count 4

# فقط IP (بدون دامنه و SNI)
python scanner.py -n 5000 --no-domain --no-sni-scan

# فقط دامنه
python scanner.py --no-neighbor --no-sni-scan

# محدود کردن SNI
python scanner.py --sni-limit 20

# پورت دلخواه
python scanner.py -p 80,443

# فایل SNI محلی
python scanner.py --sni-list my_snis.txt
```

### همه گزینه‌ها

| Flag | توضیح | پیش‌فرض |
|------|-------|---------|
| `-t`, `--timeout` | TCP timeout (s) | `1.0` |
| `-T`, `--threads` | تعداد Threads | `75` |
| `-n`, `--total` | تعداد IP تصادفی | `50000` |
| `-b`, `--neighbor` | محدودیت همسایه | `200` |
| `-p`, `--ports` | پورت‌ها (کاما-جدا) | `80` |
| `--ping-count` | تعداد پینگ | `4` |
| `--sni-limit` | محدودیت SNI | همه |
| `--no-neighbor` | بدون اسکن همسایه | - |
| `--no-domain` | بدون اسکن دامنه | - |
| `--no-sni-scan` | بدون اسکن SNI | - |
| `--sni-url` | URL دلخواه SNI | (ریموت) |
| `--sni-list` | فایل محلی SNI | - |
| `--output-dir` | پوشه خروجی | `./results` |
| `--cache-file` | فایل cache | `./colo_cache.json` |

---

## 📊 نمونه خروجی

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

## 📁 فایل‌ها

| فایل | توضیح |
|------|-------|
| `scanner.py` | اسکریپت اصلی اسکنر |
| `colo_cache.json` | کش colo |
| `results/` | پوشه خروجی |

---

## 🔗 منابع داده

- **subnetهای کلادفلر**: [ircfspace/cf-ip-ranges](https://github.com/ircfspace/cf-ip-ranges)
- **لیست دامنه‌ها**: [cf-domains.txt](https://github.com/MonsterMTA/MonsterScanner/blob/main/cf-domains.txt) (230 دامنه)
- **لیست SNI**: [sni-domains.txt](https://github.com/MonsterMTA/MonsterScanner/blob/main/sni-domains.txt) (64 دامنه)

---

## 🙏 تشکر و قدردانی

- **ircfspace** — بابت نگهداری و ارائه لیست subnetهای Cloudflare: https://github.com/ircfspace/cf-ip-ranges
- **hossein-mohseni** — بابت لیست دامنه‌های CF-Web

---

## 📝 لایسنس

MIT License

---

© 2026 MonsterMTA. تمامی حقوق محفوظ است.
