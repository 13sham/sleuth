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