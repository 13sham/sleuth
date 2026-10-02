#!/usr/bin/env python3
"""
Sleuth - all-in-one OSINT terminal tool (Termux / Linux / macOS)
Use only on targets you have permission to research. Public data only.

Install (Termux):
  pkg install python -y
  pip install requests phonenumbers pillow

Run:
  python sleuth.py              # interactive menu
  python sleuth.py phone +14155552671
  python sleuth.py user johndoe
  python sleuth.py email a@b.com
  python sleuth.py domain example.com
  python sleuth.py ip 8.8.8.8
  python sleuth.py exif photo.jpg
  python sleuth.py wayback example.com
  python sleuth.py dork "John Doe"
  python sleuth.py hash <hash>
"""
import sys, re, json, socket, hashlib, datetime, urllib.parse
from concurrent.futures import ThreadPoolExecutor

try:
    import requests
except ImportError:
    sys.exit("Missing: pip install requests")

try:
    import phonenumbers
    from phonenumbers import carrier, geocoder, timezone
except ImportError:
    phonenumbers = None

try:
    from PIL import Image
    from PIL.ExifTags import TAGS, GPSTAGS
except ImportError:
    Image = None

UA = {"User-Agent": "Mozilla/5.0 (Linux; Android 13) Sleuth/1.0"}
R, G, Y, C, B, X = "\033[91m", "\033[92m", "\033[93m", "\033[96m", "\033[1m", "\033[0m"
REPORT = {}

BANNER = f"""{C}{B}
 ____  _      _____ _   _ _____ _   _
/ ___|| |    | ____| | | |_   _| | | |
\\___ \\| |    |  _| | | | | | | | |_| |
 ___) | |___ | |___| |_| | | | |  _  |
|____/|_____||_____|\\___/  |_| |_| |_|
{X}{Y} all-in-one OSINT toolkit | public data only | be ethical{X}
"""


def say(label, val):
    print(f"  {G}{label:<16}{X}{val}")


def head(t):
    print(f"\n{B}{C}== {t} =={X}")


def get(url, **kw):
    try:
        return requests.get(url, headers=UA, timeout=kw.pop("timeout", 12), **kw)
    except Exception:
        return None


def save(key, data):
    REPORT[key] = data


# ---------------------------------------------------------------- PHONE
def phone(num):
    head(f"PHONE: {num}")
    if not phonenumbers:
        print(f"{R}pip install phonenumbers{X}")
        return
    try:
        p = phonenumbers.parse(num, None)
    except Exception as e:
        print(f"{R}Parse error: {e} (use +countrycode format){X}")
        return
    info = {
        "valid": phonenumbers.is_valid_number(p),
        "possible": phonenumbers.is_possible_number(p),
        "country_code": p.country_code,
        "region": phonenumbers.region_code_for_number(p),
        "location": geocoder.description_for_number(p, "en"),
        "carrier": carrier.name_for_number(p, "en") or "unknown",
        "timezones": list(timezone.time_zones_for_number(p)),
        "type": str(phonenumbers.number_type(p)).split(".")[-1],
        "international": phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
        "national": phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.NATIONAL),
        "e164": phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164),
    }
    for k, v in info.items():
        say(k, v)
    e164 = info["e164"].lstrip("+")
    print(f"\n  {Y}Search / dork links:{X}")
    q = urllib.parse.quote
    for n, u in {
        "Google": f'https://www.google.com/search?q="{q(info["international"])}"',
        "Google (e164)": f'https://www.google.com/search?q="{q(info["e164"])}"',
        "WhatsApp": f"https://wa.me/{e164}",
        "Telegram": f"https://t.me/+{e164}",
        "Truecaller": f"https://www.truecaller.com/search/{info['region'].lower()}/{e164}",
        "Sync.me": f"https://sync.me/search/?number={e164}",
    }.items():
        say(n, u)
    save("phone", info)


# ------------------------------------------------------------- USERNAME
SITES = {
    "GitHub": "https://github.com/{}",
    "GitLab": "https://gitlab.com/{}",
    "Twitter/X": "https://x.com/{}",
    "Instagram": "https://www.instagram.com/{}/",
    "TikTok": "https://www.tiktok.com/@{}",
    "Reddit": "https://www.reddit.com/user/{}",
    "YouTube": "https://www.youtube.com/@{}",
    "Twitch": "https://www.twitch.tv/{}",
    "Pinterest": "https://www.pinterest.com/{}/",
    "Medium": "https://medium.com/@{}",
    "Dev.to": "https://dev.to/{}",
    "Telegram": "https://t.me/{}",
    "Steam": "https://steamcommunity.com/id/{}",
    "SoundCloud": "https://soundcloud.com/{}",
    "Spotify": "https://open.spotify.com/user/{}",
    "Keybase": "https://keybase.io/{}",
    "HackerOne": "https://hackerone.com/{}",
    "Replit": "https://replit.com/@{}",
    "Pastebin": "https://pastebin.com/u/{}",
    "Flickr": "https://www.flickr.com/people/{}",
    "Vimeo": "https://vimeo.com/{}",
    "About.me": "https://about.me/{}",
    "Gravatar": "https://en.gravatar.com/{}",
    "Linktree": "https://linktr.ee/{}",
    "Behance": "https://www.behance.net/{}",
    "Dribbble": "https://dribbble.com/{}",
    "Patreon": "https://www.patreon.com/{}",
    "NPM": "https://www.npmjs.com/~{}",
    "PyPI": "https://pypi.org/user/{}/",
    "Docker Hub": "https://hub.docker.com/u/{}",
}


def username(name):
    head(f"USERNAME: {name}")

    def chk(item):
        site, url = item[0], item[1].format(name)
        r = get(url, allow_redirects=True, timeout=8)
        return site, url, (r is not None and r.status_code == 200)

    with ThreadPoolExecutor(15) as ex:
        res = list(ex.map(chk, SITES.items()))
    found = [(s, u) for s, u, ok in res if ok]
    for s, u in found:
        say(s, u)
    print(f"\n  {Y}{len(found)}/{len(SITES)} hits. Some sites return 200 for any name "
          f"(false positives) - verify manually.{X}")
    save("username", dict(found))


# ---------------------------------------------------------------- EMAIL
def doh(name, rtype):
    r = get(f"https://dns.google/resolve?name={name}&type={rtype}")
    try:
        return [a["data"] for a in r.json().get("Answer", [])]
    except Exception:
        return []


DISPOSABLE = {"mailinator.com", "10minutemail.com", "guerrillamail.com", "tempmail.com",
              "yopmail.com", "trashmail.com", "sharklasers.com", "getnada.com", "throwawaymail.com"}


def email(addr):
    head(f"EMAIL: {addr}")
    if not re.match(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$", addr):
        print(f"{R}Invalid syntax{X}")
        return
    user, dom = addr.lower().split("@")
    mx = doh(dom, "MX")
    say("syntax", "ok")
    say("domain", dom)
    say("MX records", ", ".join(mx) if mx else "NONE (can't receive mail)")
    say("SPF", next((t for t in doh(dom, "TXT") if "v=spf1" in t), "none"))
    say("disposable", "YES" if dom in DISPOSABLE else "no")
    h = hashlib.md5(addr.lower().encode()).hexdigest()
    g = get(f"https://www.gravatar.com/avatar/{h}?d=404")
    say("gravatar", f"https://gravatar.com/{h}" if g is not None and g.status_code == 200 else "none")
    say("username part", user)
    q = urllib.parse.quote
    say("Google dork", f'https://www.google.com/search?q="{q(addr)}"')
    say("breach check", f"https://haveibeenpwned.com/account/{q(addr)}")
    save("email", {"mx": mx, "gravatar_hash": h})


# --------------------------------------------------------------- DOMAIN
def domain(d):
    head(f"DOMAIN: {d}")
    d = re.sub(r"^https?://|/.*$", "", d)
    data = {}
    for t in ("A", "AAAA", "MX", "NS", "TXT", "CNAME"):
        v = doh(d, t)
        data[t] = v
        if v:
            say(t, " | ".join(v)[:200])
    r = get(f"https://rdap.org/domain/{d}", timeout=15)
    if r is not None and r.status_code == 200:
        j = r.json()
        for ev in j.get("events", []):
            say(ev.get("eventAction", ""), ev.get("eventDate", ""))
        say("status", ", ".join(j.get("status", [])))
        say("nameservers", ", ".join(n["ldhName"] for n in j.get("nameservers", [])))
    print(f"\n  {Y}Subdomains (crt.sh):{X}")
    r = get(f"https://crt.sh/?q=%25.{d}&output=json", timeout=30)
    subs = set()
    if r is not None and r.status_code == 200:
        try:
            for row in r.json():
                for n in row["name_value"].split("\n"):
                    subs.add(n.strip().lstrip("*."))
        except Exception:
            pass
    for s in sorted(subs):
        print(f"   {s}")
    print(f"  {len(subs)} found")
    r = get(f"https://{d}", allow_redirects=True)
    if r is not None:
        print(f"\n  {Y}HTTP headers:{X}")
        for k in ("Server", "X-Powered-By", "Content-Type", "Strict-Transport-Security",
                  "Content-Security-Policy", "X-Frame-Options", "Set-Cookie"):
            if k in r.headers:
                say(k, r.headers[k][:100])
        m = re.search(r"<title[^>]*>(.*?)</title>", r.text, re.S | re.I)
        say("title", m.group(1).strip()[:100] if m else "-")
        gen = re.search(r'name=["\']generator["\'] content=["\'](.*?)["\']', r.text, re.I)
        say("generator", gen.group(1) if gen else "-")
    data["subdomains"] = sorted(subs)
    save("domain", data)


# ------------------------------------------------------------------- IP
def ip(target):
    head(f"IP: {target}")
    try:
        addr = socket.gethostbyname(target)
    except Exception:
        print(f"{R}Cannot resolve{X}")
        return
    say("resolved", addr)
    r = get(f"http://ip-api.com/json/{addr}?fields=66846719")
    if r is not None:
        j = r.json()
        for k in ("country", "regionName", "city", "zip", "lat", "lon", "timezone",
                  "isp", "org", "as", "reverse", "mobile", "proxy", "hosting"):
            if k in j:
                say(k, j[k])
        if "lat" in j:
            say("map", f"https://www.google.com/maps?q={j['lat']},{j['lon']}")
        save("ip", j)
    r = get(f"https://internetdb.shodan.io/{addr}")
    if r is not None and r.status_code == 200:
        j = r.json()
        print(f"\n  {Y}Shodan InternetDB:{X}")
        say("open ports", j.get("ports"))
        say("hostnames", j.get("hostnames"))
        say("vulns", j.get("vulns"))
        say("tags", j.get("tags"))


# ----------------------------------------------------------------- EXIF
def exif(path):
    head(f"EXIF: {path}")
    if not Image:
        print(f"{R}pip install pillow{X}")
        return
    try:
        img = Image.open(path)
        raw = img._getexif() or {}
    except Exception as e:
        print(f"{R}{e}{X}")
        return
    if not raw:
        print("  no EXIF data")
        return
    gps = {}
    for k, v in raw.items():
        tag = TAGS.get(k, k)
        if tag == "GPSInfo":
            gps = {GPSTAGS.get(a, a): v[a] for a in v}
        elif isinstance(v, (str, int, float)):
            say(str(tag), str(v)[:80])

    def deg(v, ref):
        d = float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
        return -d if ref in ("S", "W") else d

    if "GPSLatitude" in gps:
        la = deg(gps["GPSLatitude"], gps["GPSLatitudeRef"])
        lo = deg(gps["GPSLongitude"], gps["GPSLongitudeRef"])
        say("GPS", f"{la:.6f}, {lo:.6f}")
        say("map", f"https://www.google.com/maps?q={la},{lo}")


# -------------------------------------------------------------- WAYBACK
def wayback(u):
    head(f"WAYBACK: {u}")
    r = get(f"https://archive.org/wayback/available?url={u}")
    if r is not None:
        snap = r.json().get("archived_snapshots", {}).get("closest")
        say("closest", snap["url"] if snap else "none")
    r = get(f"http://web.archive.org/cdx/search/cdx?url={u}&output=json&limit=10&fl=timestamp,original,statuscode&collapse=digest")
    if r is not None:
        try:
            for row in r.json()[1:]:
                print(f"   {row[0]}  {row[2]}  https://web.archive.org/web/{row[0]}/{row[1]}")
        except Exception:
            pass


# ----------------------------------------------------------------- DORKS
def dork(term):
    head(f"DORKS: {term}")
    q = urllib.parse.quote
    t = f'"{term}"'
    dorks = {
        "Exact": t,
        "Documents": f'{t} filetype:pdf OR filetype:doc OR filetype:xls',
        "LinkedIn": f'{t} site:linkedin.com',
        "Facebook": f'{t} site:facebook.com',
        "Twitter": f'{t} site:x.com',
        "Pastebin": f'{t} site:pastebin.com',
        "GitHub": f'{t} site:github.com',
        "Forums": f'{t} inurl:forum OR inurl:thread',
        "Resume": f'{t} intitle:resume OR intitle:cv',
    }
    for n, d in dorks.items():
        say(n, f"https://www.google.com/search?q={q(d)}")


# ----------------------------------------------------------------- HASH
HASHES = {32: "MD5/NTLM", 40: "SHA-1", 56: "SHA-224", 64: "SHA-256", 96: "SHA-384", 128: "SHA-512"}


def hashid(h):
    head("HASH ID")
    h = h.strip()
    say("length", len(h))
    say("likely", HASHES.get(len(h), "unknown") if re.fullmatch(r"[a-fA-F0-9]+", h) else "not hex")
    if h.startswith(("$2a$", "$2b$", "$2y$")):
        say("likely", "bcrypt")


# ------------------------------------------------------------------ MENU
MENU = [
    ("Phone number lookup", "phone", "Phone (+countrycode...)"),
    ("Username search (30 sites)", "user", "Username"),
    ("Email analysis", "email", "Email"),
    ("Domain recon (DNS/WHOIS/subs/headers)", "domain", "Domain"),
    ("IP / host geolocation + ports", "ip", "IP or hostname"),
    ("Image EXIF / GPS", "exif", "Image path"),
    ("Wayback Machine", "wayback", "URL"),
    ("Google dork generator", "dork", "Name / keyword"),
    ("Hash identifier", "hash", "Hash"),
]
FN = {"phone": phone, "user": username, "email": email, "domain": domain, "ip": ip,
      "exif": exif, "wayback": wayback, "dork": dork, "hash": hashid}


def export():
    if not REPORT:
        return
    fn = f"sleuth_report_{datetime.datetime.now():%Y%m%d_%H%M%S}.json"
    json.dump(REPORT, open(fn, "w"), indent=2, default=str)
    print(f"\n{G}Report saved: {fn}{X}")


def menu():
    print(BANNER)
    while True:
        print()
        for i, (n, _, _) in enumerate(MENU, 1):
            print(f"  {C}[{i}]{X} {n}")
        print(f"  {C}[s]{X} Save report   {C}[0]{X} Exit")
        c = input(f"\n{B}sleuth>{X} ").strip().lower()
        if c == "0":
            break
        if c == "s":
            export()
            continue
        if c.isdigit() and 1 <= int(c) <= len(MENU):
            _, key, prompt = MENU[int(c) - 1]
            v = input(f"  {prompt}: ").strip()
            if v:
                FN[key](v)


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] in FN:
        FN[a[0]](" ".join(a[1:]))
        export()
    else:
        try:
            menu()
        except (KeyboardInterrupt, EOFError):
            print()
  
