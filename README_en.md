# MonsterScanner

ابزاری برای اسکن IPها و دامنه‌های کلادفلر و اندازه‌گیری latency و packet loss از ایران.

## ویژگی‌ها

- **اسکن IP تصادفی** — اسکن IPهای تصادفی از رنج‌های کلادفلر
- **اسکن همسایه** — وقتی IP معتبری پیدا میشه، همسایه‌ها رو هم اسکن میکنه
- **تست دامنه** — تست دامنه‌های واقعی پشت کلادفلر
- **SNI Spoofing** — تست دامنه‌های SNI (hcaptcha, cdns و...)
- **TCP 3-Way Handshake** — پینگ واقعی TCP برای دقت بالا
- **Packet Loss Tracking** — نمایش درصد پکت لاس و jitter
- **Colo Cache** — ذخیره کش colo بین اجراها
- **چند Threads** — اسکن موازی با Thread قابل تنظیم

## پیش‌نیازها

- Python 3.11+
- بدون وابستگی خارجی (فقط کتابخانه استاندارد)

## نصب

```bash
git clone https://github.com/MonsterMTA/MonsterScanner.git
cd MonsterScanner
# نیازی به pip install نیست
```

## نحوه استفاده

### استفاده ساده

```bash
python scanner.py
```

### گزینه‌های پرکاربرد

```bash
# تست سریع
python scanner.py -n 100 -T 10 --ping-count 2

# اسکن کامل
python scanner.py -n 50000 -T 75 --ping-count 4

# فقط IP (بدون دامنه و SNI)
python scanner.py -n 5000 --no-domain --no-sni-scan

# فقط دامنه
python scanner.py --no-neighbor --no-domain --no-sni-scan

# محدود کردن SNI
python scanner.py --sni-limit 20

# پورت‌های دلخواه
python scanner.py -p 80,443

# لیست SNI محلی
python scanner.py --sni-list my_snis.txt
```

### آرگومان‌های CLI

| فلگ | توضیح | پیش‌فرض |
|------|-------|---------|
| `-t`, `--timeout` | TCP timeout (ثانیه) | `1.0` |
| `-T`, `--threads` | تعداد Threads | `75` |
| `-n`, `--total` | تعداد IP تصادفی | `50000` |
| `-b`, `--neighbor` | محدودیت همسایه | `200` |
| `-p`, `--ports` | پورت‌ها (کاما-جدا) | `80` |
| `--subnets-url` | URL subnet list | (ریموت) |
| `--domains-url` | URL دامنه‌ها | (ریموت) |
| `--sni-url` | URL SNI دامنه‌ها | (ریموت) |
| `--sni-list` | فایل محلی SNI | - |
| `--ping-count` | تعداد پینگ | `4` |
| `--sni-limit` | محدودیت SNI | همه |
| `--output-dir` | پوشه خروجی | `./results` |
| `--cache-file` | مسیر cache | `./colo_cache.json` |
| `--no-neighbor` | بدون اسکن همسایه | - |
| `--no-domain` | بدون اسکن دامنه | - |
| `--no-sni-scan` | بدون اسکن SNI | - |

## منابع داده

### لیست دامنه‌ها
- **دامنه‌های اصلی**: https://github.com/MonsterMTA/MonsterScanner/blob/main/cf-domains.txt (230 دامنه)
- **SNI دامنه‌ها**: https://github.com/MonsterMTA/MonsterScanner/blob/main/sni-domains.txt (64 دامنه)

### subnetهای کلادفلر
- **منبع**: https://github.com/ircfspace/cf-ip-ranges
- **تعداد subnetها**: 4661
- **توضیح**: این لیست شامل تمام subnetهای فعال Cloudflare Flare (IPv4) است که توسط ircfspace نگهداری و به‌روز می‌شود. تشکر و قدردانی از ircfspace بابت نگهداری و ارائه این لیست رایگان.

## خروجی

### فرمت نتایج

نتایج در `results/valid_ips_YYYY-MM-DD_HH-MM-SS.txt` ذخیره میشن:
```
# Valid Cloudflare IPs — 2026-08-13 18:10:01
# Format: IP:PORT
# ==================================================
104.16.10.5:80
172.67.20.3:80
```

### خروجی کنسول

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

## نحوه کار

### Phase 1: اسکن IP تصادفی
- تولید IP تصادفی از رنج‌های /8 کلادفلر (104.16.0.0/12, 172.64.0.0/10)
- TCP handshake ping به هر IP
- اعتبارسنجی با `/cdn-cgi/trace`

### Phase 2: اسکن همسایه
- وقتی IP معتبری پیدا میشه، همسایه‌های همان /24 اسکن میشن
- hop-based approach: هر subnet یک‌دفعه
- محدودیت کلی برای جلوگیری از اسکن بیش‌ازحد

### Phase 3: تست دامنه
- resolve دامنه‌ها به IP کلادفلر
- TCP handshake ping
- اعتبارسنجی پاسخ کلادفلر

### Phase 4: SNI Spoofing
- تست دامنه‌های SNI (مثل hcaptcha.com, cdns)
- useful برای پیدا کردن endpointهای کم‌latency

### Packet Loss
- هر پینگ N بار handshake TCP انجام میده (پیش‌فرض: 4)
- timeoutها به عنوان packet loss شمارش میشن
- نمایش درصد لاس و min/max RTT

## Colo Cache

اطلاعات colo در `colo_cache.json` ذخیره میشه:
- بار اول: همه lookups HTTP هستند
- اجراهای بعدی: cache hit باعث صرفه‌جویی در زمان میشه

## لایسنس

MIT License

## تشکر و قدردانی

- **ircfspace** — برای نگهداری و ارائه لیست subnetهای Cloudflare: https://github.com/ircfspace/cf-ip-ranges
- **hossein-mohseni** — برای لیست دامنه‌های CF-Web

---

© 2026 MonsterMTA. تمامی حقوق محفوظ است.
