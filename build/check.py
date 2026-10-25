"""Verifies the built site against a local server that mirrors the canonical
base path, then builds a throwaway production copy to confirm the mode flip.

    ./build.sh check

Checks: every URL in sitemap.xml, robots.txt and llms.txt returns 200; every
internal href/src on every page returns 200; og:image is 1200x630; robots meta
matches the deployment mode; JSON-LD parses; no placeholder text; every order
button lands on order.html.
"""
import functools
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.parse
import urllib.request
from io import BytesIO

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = json.load(open(os.path.join(ROOT, "site.config.json")))
MODE = CONFIG["deployment_mode"]
BASE = CONFIG["canonical_base"][MODE].rstrip("/")
PATH = urllib.parse.urlparse(BASE).path  # "" for production, "/eatfit" for review
PAGES = [f for f in os.listdir(ROOT) if f.endswith(".html")]
PLACEHOLDER = re.compile(r"\b(TBD|TODO|lorem|ipsum|placeholder|XXX|None|null|undefined|NaN)\b", re.I)
fails = []


def fail(msg):
    fails.append(msg)
    print("FAIL", msg)


def serve():
    # Serve the repo at PATH so local URLs mirror BASE exactly.
    tmp = tempfile.mkdtemp()
    target = os.path.join(tmp, PATH.strip("/")) if PATH else tmp
    if PATH:
        os.symlink(ROOT, target)
    else:
        os.rmdir(tmp)
        tmp = ROOT
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=tmp)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_port}"


def get(local, u):
    lu = u.replace(BASE, local + PATH, 1) if u.startswith(BASE) else u
    try:
        with urllib.request.urlopen(lu, timeout=10) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def main():
    local = serve()
    # 1. URLs referenced by the indexing files.
    refs = set()
    refs |= set(re.findall(r"<loc>([^<]+)</loc>", open(os.path.join(ROOT, "sitemap.xml")).read()))
    refs |= set(re.findall(r"https?://\S+", open(os.path.join(ROOT, "robots.txt")).read()))
    for f in ("llms.txt", "llms-full.txt"):
        refs |= {u.rstrip(").,") for u in re.findall(r"https?://[^\s)]+", open(os.path.join(ROOT, f)).read())
                 if u.startswith(BASE)}
    for u in sorted(u for u in refs if u.startswith(BASE)):
        status, _ = get(local, u)
        if status != 200:
            fail(f"{status} {u}")
    print(f"indexing files: {len([u for u in refs if u.startswith(BASE)])} canonical-base URLs checked")

    # 2. og:image
    status, data = get(local, BASE + "/assets/img/share-logo.jpg")
    size = Image.open(BytesIO(data)).size if status == 200 else None
    if status != 200 or size != (1200, 630):
        fail(f"og:image status={status} size={size}")
    else:
        print("og:image: 200, 1200x630")

    # 3. Per page checks.
    internal = set()
    for p in sorted(PAGES):
        html = open(os.path.join(ROOT, p), encoding="utf-8").read()
        noindex = '<meta name="robots" content="noindex,nofollow">' in html
        want = MODE == "review" or p == "404.html"
        if noindex != want:
            fail(f"{p}: noindex={noindex}, expected {want}")
        canon = re.search(r'<link rel="canonical" href="([^"]+)"', html).group(1)
        if not canon.startswith(BASE):
            fail(f"{p}: canonical {canon} not on {BASE}")
        for blob in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
            try:
                ld = json.loads(blob)
            except ValueError as e:
                fail(f"{p}: JSON-LD does not parse: {e}")
                continue
            if PLACEHOLDER.search(json.dumps(ld)):
                fail(f"{p}: placeholder-like value in JSON-LD")
        text = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->|<[^>]+>", " ", html, flags=re.S)
        m = PLACEHOLDER.search(text)
        if m:
            fail(f"{p}: placeholder-like text {m.group(0)!r}")
        for ref in re.findall(r'(?:href|src|srcset)="([^"#?]+)', html):
            if not re.match(r"(https?:|mailto:|tel:)", ref):
                internal.add(ref)
        # Order buttons must go to a configured platform link, or to the #order boxes.
        allowed = set(CONFIG["order_links"][k] for k in CONFIG["platforms"])
        for block in re.findall(r'<div class="order" id="order">.*?</div></div>', html, re.S):
            for h in re.findall(r'href="([^"]+)"', block):
                if h.replace("&amp;", "&") not in allowed:
                    fail(f"{p}: order box goes to {h}")
        for h in re.findall(r'class="btn sm hdr-order" href="([^"]+)"', html):
            if h not in ("#order", "./#order"):
                fail(f"{p}: header order button goes to {h}")
    for ref in sorted(internal):
        status, _ = get(local, f"{BASE}/{ref.lstrip('./')}" if ref not in ("./",) else BASE + "/")
        if status != 200:
            fail(f"internal link {status} {ref}")
    print(f"pages: {len(PAGES)} checked, {len(internal)} internal links/assets checked")

    # 4. Mode flip: build a production copy elsewhere and compare.
    with tempfile.TemporaryDirectory() as out:
        cfg = dict(CONFIG, deployment_mode="production" if MODE == "review" else "review")
        cpath = os.path.join(out, "config.json")
        json.dump(cfg, open(cpath, "w"))
        env = dict(os.environ, EATFIT_CONFIG=cpath, EATFIT_OUT=out)
        subprocess.run([sys.executable, os.path.join(ROOT, "build", "generate.py")], check=True, env=env,
                       stdout=subprocess.DEVNULL)
        other_base = cfg["canonical_base"][cfg["deployment_mode"]].rstrip("/")
        for p in sorted(PAGES):
            html = open(os.path.join(out, p), encoding="utf-8").read()
            noindex = "noindex" in html
            if cfg["deployment_mode"] == "production" and noindex and p != "404.html":
                fail(f"production build {p} still has noindex")
            if BASE in html:
                fail(f"{cfg['deployment_mode']} build {p} still mentions {BASE}")
            if other_base not in html:
                fail(f"{cfg['deployment_mode']} build {p} missing {other_base}")
        for f in ("robots.txt", "sitemap.xml", "llms.txt", "llms-full.txt"):
            if BASE in open(os.path.join(out, f)).read():
                fail(f"{cfg['deployment_mode']} build {f} still mentions {BASE}")
        print(f"mode flip: {cfg['deployment_mode']} build checked ({other_base})")

    print("ALL CHECKS PASSED" if not fails else f"{len(fails)} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
