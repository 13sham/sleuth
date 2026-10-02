# Sleuth

All-in-one OSINT terminal tool for **Termux, Linux, and macOS**. One Python file, no API keys needed.

Public data only. Use responsibly.

## Features

| Command | What it does |
|---|---|
| `phone` | Validity, carrier, region, timezone, number formats, WhatsApp/Telegram/Truecaller/Google search links |
| `user` | Checks a username across 30 sites (GitHub, Instagram, Reddit, TikTok, etc.) |
| `email` | Syntax check, MX and SPF records, disposable-domain check, Gravatar, breach-check link |
| `domain` | DNS records, WHOIS/RDAP, subdomains (crt.sh), HTTP headers, page title and generator |
| `ip` | Geolocation, ISP/ASN, reverse DNS, open ports and vulns (Shodan InternetDB) |
| `exif` | Image metadata and GPS coordinates with a map link |
| `wayback` | Wayback Machine snapshots for a URL |
| `dork` | Generates Google dork links for a name or keyword |
| `hash` | Identifies likely hash type by length and format |

Reports can be exported to JSON.

## Install

### Termux (Android)

```bash
pkg update && pkg install python git -y
git clone https://github.com/YOURNAME/sleuth
cd sleuth
pip install -r requirements.txt
python sleuth.py
```

To read photos from your phone storage, run `termux-setup-storage` once.

### Linux / macOS

```bash
git clone https://github.com/YOURNAME/sleuth
cd sleuth
pip install -r requirements.txt
python3 sleuth.py
```

## Usage

### Interactive menu

```bash
python sleuth.py
```

Pick a number, enter the target. Press `s` to save a JSON report, `0` to exit.

### Direct commands

```bash
python sleuth.py phone +14155552671
python sleuth.py user johndoe
python sleuth.py email name@example.com
python sleuth.py domain example.com
python sleuth.py ip 8.8.8.8
python sleuth.py exif ~/storage/downloads/photo.jpg
python sleuth.py wayback example.com
python sleuth.py dork "John Doe"
python sleuth.py hash 5f4dcc3b5aa765d61d8327deb882cf99
```

CLI runs save a `sleuth_report_<timestamp>.json` automatically.

## Notes and limitations

- **Phone:** numbers must include the country code (`+44...`). Carrier data reflects the original carrier and does not account for number porting. Results are not a live location.
- **Username:** some sites return HTTP 200 for any name, so verify hits manually.
- **IP geolocation** is approximate (usually city level) and often points to the ISP, not a person.
- **Rate limits:** free APIs (ip-api.com, crt.sh) may throttle heavy use.
- **EXIF:** most social platforms strip metadata, so original files work best.
- Sites change their layouts, so some checks may need updating over time.

## Data sources

Google DNS-over-HTTPS, RDAP, crt.sh, ip-api.com, Shodan InternetDB, Gravatar, Internet Archive, and the `phonenumbers` library.

## Roadmap ideas

- Plugin system (`modules/` folder)
- Reverse image search links
- Email permutation generator
- PDF/DOCX metadata extraction
- Crypto wallet lookup
- GitHub recon (commit emails, org members)
- Tech stack detection
- `--json` flag, `rich` tables, proxy/Tor option

Contributions and pull requests are welcome.

## Legal disclaimer

This tool is for **education, security research, journalism, and authorized investigations**. It only queries publicly available information.

- You are responsible for how you use it.
- Do not use it to stalk, harass, dox, or harm anyone.
- Follow the laws and terms of service that apply to you and to the services queried.
- The author accepts no liability for misuse or damages.

## License

MIT. See `LICENSE`.
