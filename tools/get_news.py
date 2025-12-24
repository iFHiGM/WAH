import urllib.request
import re

def get_npr():
    try:
        url = "https://text.npr.org/"
        # Use a generic user agent to avoid blocking
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as f:
            html = f.read().decode('utf-8')
            # Extract headlines from NPR text site
            items = re.findall(r'<a class="topic-title"[^>]*>(.*?)</a>', html)
            return ["NPR: " + i.strip() for i in items[:5]]
    except Exception as e:
        return [f"NPR Error: {e}"]

def get_cnn():
    try:
        url = "https://lite.cnn.com/"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as f:
            html = f.read().decode('utf-8')
            # Extract headlines from CNN Lite
            items = re.findall(r'<li[^>]*><a[^>]*>(.*?)</a>', html)
            return ["CNN: " + i.strip() for i in items[:5]]
    except Exception as e:
        return [f"CNN Error: {e}"]

if __name__ == "__main__":
    print("--- HEADLINES ---")
    for h in get_npr(): print(h)
    for h in get_cnn(): print(h)