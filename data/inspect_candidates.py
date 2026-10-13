import re
import httpx

import glob

report_files = sorted(glob.glob("reports/daily_report_*.md"))
latest_report = report_files[-1] if report_files else "reports/daily_report_2026-10-10.md"
print(f"Inspecting links in: {latest_report}")

with open(latest_report, "r", encoding="utf-8") as f:
    text = f.read()

urls = sorted(list(set(re.findall(r"https?://[^\s\)\"\>]+", text))))
print(f"Total distinct links found in report: {len(urls)}\n")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}

all_ok = True
for url in urls:
    try:
        r = httpx.get(url, headers=headers, follow_redirects=True, timeout=10.0)
        status = r.status_code
        print(f"[{status}] {url}")
        if status not in [200, 301, 302]:
            all_ok = False
    except Exception as e:
        print(f"[FAIL] {url} -> {e}")
        all_ok = False

print("\n-------------------------------------------")
if all_ok:
    print("SUCCESS: 100% OF ALL LINKS IN THE REPORT ARE VERIFIED LIVE (HTTP 200)!")
else:
    print("WARNING: Some links failed validation.")
