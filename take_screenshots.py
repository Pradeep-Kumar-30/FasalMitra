"""
Take screenshots of FasalMitra HTML pages using headless Chrome.
Saves to images/ folder with descriptive names.
"""
import subprocess
import os
import time

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE_DIR = r"c:\Users\DELL\Desktop\Fasal-Mitra"
OUT_DIR = os.path.join(BASE_DIR, "images")

# Pages to screenshot: (filename, output_name, description)
PAGES = [
    ("index.html",           "ss_01_home.png",        "FasalMitra Homepage"),
    ("disease.html",         "ss_02_disease.png",     "Disease Detection"),
    ("crop.html",            "ss_03_crop.png",        "Crop Recommendation"),
    ("weather.html",         "ss_04_weather.png",     "Weather Dashboard"),
    ("marketplace.html",     "ss_05_marketplace.png", "Marketplace"),
    ("scheme.html",          "ss_06_schemes.png",     "Government Schemes"),
    ("community_forum.html", "ss_07_community.png",   "Community Forum"),
    ("farm_dashboard.html",  "ss_08_dashboard.png",   "Farm Dashboard"),
    ("chat.html",            "ss_09_chat.png",        "AI Chat Assistant"),
    ("loan_dashboard.html",  "ss_10_loan.png",        "Loan Dashboard"),
]

def screenshot(html_file, out_name):
    url = f"file:///{BASE_DIR}/{html_file}".replace("\\", "/")
    out_path = os.path.join(OUT_DIR, out_name)
    cmd = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        f"--screenshot={out_path}",
        "--window-size=1280,800",
        "--virtual-time-budget=3000",
        url
    ]
    print(f"  Capturing: {html_file} → {out_name}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if os.path.exists(out_path):
            size = os.path.getsize(out_path)
            print(f"  ✅ Saved {out_name} ({size:,} bytes)")
            return True
        else:
            print(f"  ❌ File not created for {html_file}")
            print(f"     stderr: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ⏰ Timeout for {html_file}")
        return False
    except Exception as e:
        print(f"  ❌ Error for {html_file}: {e}")
        return False

if __name__ == "__main__":
    print(f"=== FasalMitra Screenshot Tool ===")
    print(f"Output dir: {OUT_DIR}")
    os.makedirs(OUT_DIR, exist_ok=True)
    
    success = 0
    for html_file, out_name, desc in PAGES:
        full_path = os.path.join(BASE_DIR, html_file)
        if not os.path.exists(full_path):
            print(f"  ⚠️  Skipping {html_file} (not found)")
            continue
        if screenshot(html_file, out_name):
            success += 1
        time.sleep(1)  # small delay between pages
    
    print(f"\n=== Done: {success}/{len(PAGES)} screenshots saved ===")
    
    # List all ss_ files
    print("\nScreenshot files in images/:")
    for f in sorted(os.listdir(OUT_DIR)):
        if f.startswith("ss_"):
            size = os.path.getsize(os.path.join(OUT_DIR, f))
            print(f"  {f}: {size:,} bytes")
