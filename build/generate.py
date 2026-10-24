"""Builds the EatFit site from site.config.json + build/menu_live.tsv + build/posts.py.

Run ./build.sh from the repo root (it also refreshes derived images). The page
templates live in this file; every URL, mode and brand fact comes from
site.config.json, so nothing here hardcodes the canonical base.
"""
import csv
import re
import json
import os
from datetime import date
from html import escape

from posts import POSTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# EATFIT_CONFIG / EATFIT_OUT let build/check.py build a second copy (e.g. production mode) elsewhere.
CONFIG = json.load(open(os.environ.get("EATFIT_CONFIG", os.path.join(ROOT, "site.config.json")), encoding="utf-8"))
OUT = os.environ.get("EATFIT_OUT", ROOT)

MODE = CONFIG["deployment_mode"]
if MODE not in ("production", "review"):
    raise SystemExit(f"deployment_mode must be 'production' or 'review', got {MODE!r}")
BASE = CONFIG["canonical_base"][MODE].rstrip("/")
AI_POLICY = CONFIG["robots_ai_policy"]
if AI_POLICY not in ("allow-all", "retrieval-only", "block-training"):
    raise SystemExit(f"robots_ai_policy must be allow-all, retrieval-only or block-training, got {AI_POLICY!r}")

BRAND = CONFIG["brand"]
NAME = BRAND["name"]
TAGLINE = BRAND["tagline"]
HASHTAG = BRAND["hashtag"]
INSTAGRAM = BRAND["instagram"]
CUREFOODS = BRAND["parent_url"]
ADDRESS = BRAND["address_lines"]
BRANDS = BRAND["sub_brands"]
CITIES = [c for c in CONFIG["cities"] if c["listed_on_site"]]
CITY_NAMES = [c["name"] for c in CITIES]
PLATFORMS = CONFIG["platforms"]
ORDER_LINKS = CONFIG["order_links"]
CONTACT = CONFIG["contact"]
TRUST = CONFIG["trust"]
MENU_CFG = CONFIG["menu"]
MENU_DATE = MENU_CFG["last_changed"]
DISH = MENU_CFG["dish_details"]

# Menu sections, in display order: (title, source categories, note)
SECTIONS = [
    ("Fusion Bowls", ["Fusion Bowls"], "Global flavours, balanced bowls."),
    ("Homely Bowls", ["Homely Bowls"], "Dal-chawal, rajma-chawal, the everyday classics."),
    ("Curry & Rice Bowls", ["Indian Bowls"], "Your favourite curry with steamed rice."),
    ("Khichdi", ["Homely Khichdi"], "Comforting, protein-rich, never boring."),
    ("Curries", ["Fit Curry", "Soya Chaap Gravies"], "Calorie-counted gravies to pair with rice or roti."),
    ("Curd Rice", ["Classic Curd Rice"], "Cool, light and South Indian."),
    ("All-Day Breakfast", ["All Day Breakfast"], "Dosa and idli, any time of day."),
    ("Sugar-free Ice Cream", ["Guiltfree Icecream by Papacream"], "Guilt-free desserts by Papacream."),
    ("Drinks", ["Beverages", "Juices", "LQD Salad"], "Shakes, juices and coolers."),
]
SKIP_ITEMS = {"Diet Coke"}
NON_VEG = ("chicken", "meatball", "carne", "egg", "mutton", "fish")
TIDY = {
    "Jain Vegetable Khichdi (Shravan Special)": "Jain Vegetable Khichdi",
    "Lasooni Methi Paneer with Steam rice": "Lasooni Methi Paneer with Steam Rice",
    "Steam Rice with Kadhai Soya chaap": "Steam Rice with Kadhai Soya Chaap",
    "Italian Chunky Veggie bowl": "Italian Chunky Veggie Bowl",
    "Protein Milk Shake -Chocolate (25g)": "Protein Milkshake, Chocolate (25g protein)",
    "Protein Milk Shake -Vanilla (25g)": "Protein Milkshake, Vanilla (25g protein)",
    "Idli-Sambhar with Chutney (Gluten-Free)": "Idli Sambar with Chutney (Gluten-free)",
    "Idli and Vada with Sambar": "Idli & Vada with Sambar",
    "LQD Salad High Fibre Drink": "LQD Salad, High-Fibre Drink",
    "Sugarfree Belgian Choco Chunk 100ml": "Belgian Choco Chunk (100ml)",
    "Sugarfree Strawberry Crumble 100ml": "Strawberry Crumble (100ml)",
    "Sugarfree Espresso Cookie 100ml": "Espresso Cookie (100ml)",
    "Sugarfree Vanilla Mudpie 100ml": "Vanilla Mudpie (100ml)",
}

# Health claims already on the site. Kept as-is, not repeated anywhere new,
# pending verification (NEEDS-INPUT #H1-#H5).
PHILOSOPHY = [
    ("Better processes", ["ISO-certified kitchens", "Farm-to-fork tracking",
                          "Calorie counted", "Nutritionist approved"]),
    ("Better ingredients", ["Zero trans fats", "Zero chemicals",
                            "Whole grains", "Zero deep frying"]),
]
FAQ = [
    (f"What is {NAME}?",
     f"{NAME}, by Curefoods, serves honest, clean and tasty Indian and global comfort meals made "
     "with healthy ingredients and no preservatives."),
    (f"What are {NAME}'s most popular dishes?",
     "Classic Rajma Chawal, Homely Vegetable Khichdi, Creamy Pesto Paneer Bowl, Quinoa Khichdi and "
     "Classic Curd Rice. Khichdi is our most-ordered category."),
    (f"Which cities is {NAME} available in?",
     ", ".join(CITY_NAMES[:-1]) + " and " + CITY_NAMES[-1] + "."),
    (f"Where can I order {NAME} online?",
     f"On Swiggy, Zomato and Ownly. Search for \"{NAME}\" in the app."),
    (f"What is the most popular {NAME} dish in my city?",
     "Rajma Chawal in Delhi NCR, Chandigarh and Coimbatore; Vegetable Khichdi in Bengaluru and Pune; "
     "Quinoa Khichdi in Hyderabad; Curd Rice in Mumbai; Pesto Paneer Bowl in Chennai."),
    ("What should I order for a healthy lunch?",
     "Lunch is our busiest meal. Top picks: Rajma Chawal, Dal Tadka Chawal and the Creamy Pesto Paneer Bowl."),
    ("What is a good light dinner option?",
     "Khichdi is our top dinner pick. Try Homely Vegetable, Quinoa or Simple Dal Khichdi."),
    (f"Is {NAME} food calorie-counted?",
     "Yes, and nutritionist-approved. Nutrition details are on each dish in the ordering app."),
    (f"Is {NAME} good if I'm watching my weight?",
     "Our meals are portion-controlled and never deep fried, which makes them an easy everyday choice."),
    (f"Does {NAME} have high-protein meals?",
     "Yes. Paneer, chicken and soya chaap bowls, rajma and chana meals, and Protein Milkshakes with 25g protein."),
    ("Are there vegetarian and Jain options?",
     "Most of the menu is vegetarian. Our Jain khichdis are made without onion or garlic."),
    (f"Does {NAME} serve South Indian food?",
     "Yes. A full curd rice range, plus all-day Masala Dosa, Idli and Vada."),
    (f"Does {NAME} have healthy desserts?",
     "Yes. Sugar-free ice creams and kulfis."),
    (f"Does {NAME} use preservatives or deep frying?",
     "No. Zero deep frying, zero trans fats and zero chemicals."),
    (f"Is {NAME} part of Curefoods?",
     f"Yes. {NAME} is a Curefoods brand."),
]

# Short tags on the Most Loved cards. Order-data facts or plain descriptions
# only; no nutrition claims.
NUDGES = {
    "Creamy Pesto Paneer Bowl": "#1 Fusion Bowl",
    "Desi Dal Tadka Chawal": "Comfort classic",
    "Classic Curd Rice": "Mumbai's favourite",
    "Lasooni Methi Paneer with Steam Rice": "Bestseller",
    "Dal Makhani Chawal": "Rich & creamy",
    "Homely Vegetable Khichdi": "#1 in Bengaluru",
    "Cheesy Peri Peri Paneer Bowl": "Spicy pick",
}
# Dish photos that need replacing with real kitchen photography (NEEDS-INPUT #P1).
PHOTO_FLAGS = {
    "Dal Makhani Chawal": "near-identical plate, angle and garnish to Black Chana and Dal Tadka Chawal",
    "Black Chana with Steamed Rice": "near-identical plate, angle and garnish to Dal Makhani and Dal Tadka Chawal",
    "Desi Dal Tadka Chawal": "near-identical plate, angle and garnish to Dal Makhani and Black Chana",
    "Lasooni Methi Paneer with Steam Rice": "same plate and set-up as the three dal/chana photos",
}
# Blog posts linked from home sections (internal linking).
HOME_POST_LINKS = {"phil": "why-we-dont-deep-fry", "loved": "khichdi-never-boring"}


def tidy(name):
    return TIDY.get(name, name.replace("Sugarfree ", ""))


def load_menu():
    rows = list(csv.reader(open(os.path.join(ROOT, "build", "menu_live.tsv")), delimiter="\t"))
    by_cat = {}
    for cat, item, units in rows:
        if item in SKIP_ITEMS:
            continue
        by_cat.setdefault(cat, []).append((item, int(units)))
    sections = []
    for title, cats, note in SECTIONS:
        items = sorted((i for c in cats for i in by_cat.get(c, [])), key=lambda x: -x[1])
        if items:
            sections.append((title, note, items))
    return sections


def is_veg(name):
    return not re.search(r"\b(" + "|".join(NON_VEG) + r")\b", name.lower())


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "")).strip("-")


def nice_date(d):
    return date.fromisoformat(d).strftime("%-d %B %Y")


CSS = """
@font-face{font-family:"Poppins";font-style:normal;font-weight:500;font-display:swap;src:url(fonts/poppins-500.woff2) format("woff2")}
@font-face{font-family:"Poppins";font-style:normal;font-weight:600;font-display:swap;src:url(fonts/poppins-600.woff2) format("woff2")}
@font-face{font-family:"Poppins";font-style:normal;font-weight:700;font-display:swap;src:url(fonts/poppins-700.woff2) format("woff2")}
@font-face{font-family:"Nunito Sans";font-style:normal;font-weight:400 700;font-display:swap;src:url(fonts/nunito-sans-var.woff2) format("woff2")}
:root{--navy:#1F2A5C;--pink:#E4007C;--pink-dark:#B80064;--pink-text:#C4006B;--teal:#17A2B4;--teal-text:#0B6E7A;
--ink:#1F2A5C;--muted:#5A6079;--bg:#FFFFFF;--soft:#F5F6FA;--line:#E3E5EE;--blush:#FFF1F7;
--veg:#1E8E3E;--nonveg:#B3261E;--hdr:72px;
--head:"Poppins",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
--body:"Nunito Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
*,*::before,*::after{box-sizing:border-box}
[hidden]{display:none!important}
html{scroll-behavior:smooth;scroll-padding-top:calc(var(--hdr) + 12px)}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 var(--body);-webkit-font-smoothing:antialiased;overflow-wrap:break-word}
img{max-width:100%;display:block}
picture{display:contents}
picture>source{display:none}
a{color:inherit}
:focus-visible{outline:3px solid var(--navy);outline-offset:3px;border-radius:6px}
footer :focus-visible,.cities :focus-visible{outline-color:#fff}
.skip{position:absolute;left:12px;top:-60px;z-index:50;background:var(--navy);color:#fff;padding:10px 16px;border-radius:10px;font-family:var(--head);font-weight:600;text-decoration:none}
.skip:focus{top:12px}
main:focus{outline:none}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
h1,h2,h3{font-family:var(--head);line-height:1.15;margin:0 0 .45em;color:var(--navy)}
h1{font-size:clamp(2.1rem,5.5vw,3.5rem);font-weight:700}
h2{font-size:clamp(1.6rem,3.6vw,2.3rem);font-weight:700}
h3{font-size:1.15rem;font-weight:600}
.accent{color:var(--pink)}.hero h1 .accent{display:block}
header{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}
header .wrap{display:flex;align-items:center;gap:12px;height:var(--hdr)}
header .logo{margin-right:auto;flex:none}
header .logo img{height:34px;width:auto}
nav.desk{display:flex;align-items:center;gap:22px}
nav.desk a{position:relative;text-decoration:none;font-family:var(--head);font-weight:500;font-size:.95rem;color:var(--navy);padding:6px 0}
nav.desk a:hover{color:var(--pink-text)}
nav.desk a[aria-current]{color:var(--pink-text);font-weight:600}
nav.desk a[aria-current]::after{content:"";position:absolute;left:0;right:0;bottom:-2px;height:2px;border-radius:2px;background:var(--pink)}
.hdr-order{margin-left:10px;flex:none}
.burger{display:none;flex:none;width:44px;height:44px;border-radius:12px;border:1px solid var(--line);background:#fff;align-items:center;justify-content:center;color:var(--navy);text-decoration:none}
.burger span,.burger span::before,.burger span::after{display:block;width:20px;height:2px;border-radius:2px;background:currentColor;position:relative}
.burger span::before,.burger span::after{content:"";position:absolute;left:0}
.burger span::before{top:-6px}.burger span::after{top:6px}
.burger[aria-expanded="true"] span{background:transparent}
.burger[aria-expanded="true"] span::before{top:0;transform:rotate(45deg)}
.burger[aria-expanded="true"] span::after{top:0;transform:rotate(-45deg)}
.mnav{position:fixed;left:0;right:0;top:var(--hdr);bottom:0;background:#fff;z-index:19;overflow-y:auto;padding:12px 20px 40px}
.mnav a{display:block;text-decoration:none;font-family:var(--head);font-weight:600;font-size:1.35rem;color:var(--navy);padding:16px 4px;border-bottom:1px solid var(--line)}
.mnav a[aria-current]{color:var(--pink-text)}
.mnav .btn{display:block;text-align:center;margin-top:24px;border-bottom:0;font-size:1.05rem;color:#fff}
body.menu-open{overflow:hidden}
.btn{display:inline-block;background:var(--pink);color:#fff;text-decoration:none;font-family:var(--head);
font-weight:600;font-size:.95rem;padding:11px 22px;border-radius:999px;border:2px solid var(--pink);transition:background .15s}
.btn:hover{background:var(--pink-dark);border-color:var(--pink-dark)}
.btn.sm{padding:8px 18px;font-size:.88rem}
.order>span{display:block;font-family:var(--head);font-weight:700;font-size:.82rem;letter-spacing:.14em;text-transform:uppercase;color:var(--navy);margin-bottom:10px}
.order>div{display:grid;grid-template-columns:repeat(3,minmax(0,150px));gap:12px}
.order a{display:block;text-align:center;text-decoration:none;background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 10px;
font-family:var(--head);font-weight:700;font-size:1.05rem;box-shadow:0 5px 0 var(--navy),0 10px 18px rgba(31,42,92,.15);transition:transform .15s,box-shadow .15s}
.order a:hover{transform:translateY(3px);box-shadow:0 2px 0 var(--navy),0 5px 10px rgba(31,42,92,.15)}
.menu-head .order{margin-top:18px}
section{padding:72px 0}
.hero{position:relative;padding:0;min-height:min(640px,78vh);display:flex;align-items:center;overflow:hidden;background:#fff}
.hero img{position:absolute;top:0;left:12%;width:100%;height:100%;object-fit:cover;object-position:center;-webkit-mask-image:linear-gradient(90deg,transparent 0,#000 30%);mask-image:linear-gradient(90deg,transparent 0,#000 30%)}
.hero::before{content:"";position:absolute;inset:0;z-index:1;
background:linear-gradient(90deg,rgba(255,255,255,.97) 0,rgba(255,255,255,.94) calc(max(0px,(100% - 1120px)/2) + 600px),rgba(255,255,255,0) calc(max(0px,(100% - 1120px)/2) + 840px))}
.hero .wrap{position:relative;z-index:2;width:100%;padding-top:64px;padding-bottom:64px}
.hero-copy{max-width:600px}
.hero p{font-size:1.15rem;color:var(--muted);max-width:500px;margin:0 0 28px}
.tag{display:inline-block;font-family:var(--head);font-weight:600;font-size:.8rem;letter-spacing:.08em;
text-transform:uppercase;color:var(--teal-text);margin-bottom:12px}
.readmore{display:inline-block;margin-top:22px;font-family:var(--head);font-weight:600;color:var(--pink-text);text-decoration:none}
.readmore:hover{text-decoration:underline}
.trust{background:var(--soft);padding:22px 0}
.trust .wrap{display:flex;flex-wrap:wrap;gap:10px 28px;align-items:center;font-family:var(--head);font-weight:600}
.trust a{color:var(--navy)}
.phil{background:var(--blush);color:var(--navy)}
.phil .wrap{display:grid;grid-template-columns:1fr 1.3fr;gap:48px;align-items:center}
.phil img{border-radius:20px;width:100%;height:auto;max-width:340px;aspect-ratio:1/1;object-fit:cover;object-position:center 30%;margin:0 auto}
.phil h3{color:var(--pink-text);margin-top:24px}
.phil ul{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:1fr 1fr;gap:10px}
.phil li{background:#fff;border:1px solid #F6D3E3;box-shadow:0 1px 2px rgba(31,42,92,.05);border-radius:12px;padding:12px 14px;font-weight:600;font-size:.95rem}
.phil li::before{content:"\\2713";color:var(--teal-text);font-weight:800;margin-right:8px}
.loved{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:24px 0 32px}
.loved .card{position:relative;display:flex;flex-direction:column;text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:16px;overflow:hidden;background:#fff;transition:transform .15s,box-shadow .15s}
.loved .nudge{position:absolute;top:12px;left:12px;z-index:1;background:#C9006D;color:#fff;font-family:var(--head);font-weight:600;font-size:.78rem;padding:5px 11px;border-radius:999px;box-shadow:0 2px 8px rgba(0,0,0,.18)}
.loved em{font-style:normal;font-family:var(--head);font-weight:600;font-size:.88rem;color:var(--pink-text);padding:0 16px 16px;margin-top:auto}
.loved img{width:100%;height:auto;aspect-ratio:4/3;object-fit:cover}
.loved p{display:flex;gap:10px;align-items:flex-start;margin:0;padding:14px 16px 16px;font-weight:600;line-height:1.35}
.loved small{display:block;font-weight:400;color:var(--muted)}
.loved-foot{display:flex;flex-wrap:wrap;align-items:center;gap:12px 24px}
.loved-foot .readmore{margin-top:0}
.dot{flex:none;width:14px;height:14px;border:1.5px solid var(--veg);border-radius:3px;position:relative;margin-top:5px}
.dot::after{content:"";position:absolute;inset:2.5px;border-radius:50%;background:var(--veg)}
.dot.nv{border-color:var(--nonveg)}.dot.nv::after{background:var(--nonveg)}
.brands{padding-top:0}
.logos{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-top:20px;align-items:center}
.logos img{width:100%;height:116px;object-fit:contain;padding:10px 14px;border:1px solid var(--line);border-radius:14px;background:#fff}
.posts{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:18px}
.post{display:flex;flex-direction:column;text-decoration:none;border:1px solid var(--line);border-radius:16px;overflow:hidden;transition:border-color .15s,transform .15s}
.post img{width:100%;height:auto;aspect-ratio:16/9;object-fit:cover}
.post div{display:flex;flex-direction:column;flex:1;padding:20px 22px 22px}
.article .cover{width:100%;height:auto;aspect-ratio:16/9;object-fit:cover;border-radius:16px;margin:18px 0 8px}
.post:hover{border-color:var(--pink);transform:translateY(-2px)}
.post time,.article time{font-size:.82rem;color:var(--teal-text);font-weight:700}
.post h3{margin:8px 0 6px;font-size:1.2rem}
.post p{color:var(--muted);flex:1;margin:0 0 14px}
.post span{color:var(--pink-text);font-weight:700;font-size:.9rem}
.article{max-width:740px;padding-top:32px;padding-bottom:64px}
.article h1{font-size:clamp(1.8rem,4.5vw,2.6rem);margin-top:8px}
.article h2{font-size:1.35rem;margin:30px 0 8px}
.article p{font-size:1.06rem;color:#3A4160}
.article p a,.article .note a{color:var(--pink-text);font-weight:700}
.crumbs{font-size:.88rem;color:var(--muted);margin-bottom:16px}
.crumbs ol{list-style:none;display:flex;flex-wrap:wrap;gap:6px;padding:0;margin:0}
.crumbs li+li::before{content:"/";margin-right:6px;color:#9AA0B4}
.crumbs a{color:var(--muted)}
.more{padding-left:18px}.more a{color:var(--pink-text)}
.cities{background:linear-gradient(135deg,#C9006D,#A3005A);padding:56px 0 64px;text-align:center}
.cities .tag{color:#fff}
.cities h2{color:#fff;margin:6px 0 28px}
.cities .grid{display:grid;grid-template-columns:repeat(4,minmax(0,190px));justify-content:center;gap:18px 16px}
.cities .grid span{display:block;background:#fff;color:var(--navy);font-family:var(--head);font-weight:700;font-size:1.02rem;padding:14px 22px;border-radius:14px;
box-shadow:0 6px 0 var(--navy),0 14px 24px rgba(31,42,92,.35);transform:perspective(500px) rotateX(8deg);transition:transform .15s,box-shadow .15s}
.faq details{border-bottom:1px solid var(--line);padding:16px 0}
.faq summary{cursor:pointer;font-family:var(--head);font-weight:600;list-style:none;display:flex;justify-content:space-between;gap:16px}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";color:var(--pink-text);font-size:1.3rem;line-height:1}
.faq details[open] summary::after{content:"\\2212"}
.faq p{margin:10px 0 0;color:var(--muted)}
.menu-head{padding-top:48px;padding-bottom:8px}
.menu-head p{color:var(--muted);max-width:620px}
.stamp{font-size:.88rem;margin:-6px 0 0}
.mtools{display:flex;flex-wrap:wrap;align-items:center;gap:10px 16px;padding:18px 0 4px}
.mtools input[type=search]{flex:1 1 220px;min-width:0;font:inherit;font-size:1rem;padding:11px 16px;border:1px solid #B9BED0;border-radius:12px;color:var(--ink);background:#fff}
.vegonly{display:inline-flex;align-items:center;gap:8px;font-family:var(--head);font-weight:600;font-size:.92rem;cursor:pointer;padding:8px 4px}
.vegonly input{width:18px;height:18px;accent-color:var(--veg)}
.count{font-size:.88rem;color:var(--muted)}
.chips-wrap{position:sticky;top:var(--hdr);z-index:5;background:#fff;border-bottom:1px solid var(--line)}
.chips-wrap::after{content:"";position:absolute;top:0;right:0;bottom:1px;width:44px;pointer-events:none;background:linear-gradient(90deg,rgba(255,255,255,0),#fff)}
.chips{display:flex;gap:8px;overflow-x:auto;padding:14px 40px 14px 0;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chips a{flex:none;text-decoration:none;font-family:var(--head);font-size:.85rem;font-weight:500;padding:7px 14px;
border:1px solid var(--line);border-radius:999px;white-space:nowrap}
.chips a:hover{border-color:var(--pink);color:var(--pink-text)}
.chips a[aria-current]{background:var(--navy);border-color:var(--navy);color:#fff}
.msec{padding:40px 0 8px;scroll-margin-top:calc(var(--hdr) + 70px)}
.msec>p{color:var(--muted);margin:-4px 0 18px}
.items{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:0 32px;list-style:none;padding:0;margin:0}
.items li{display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-bottom:1px solid var(--line);scroll-margin-top:calc(var(--hdr) + 70px)}
.items .nm{display:block}
.items .ds{display:block;font-size:.9rem;color:var(--muted)}
.items .facts{display:block;font-size:.85rem;color:var(--muted)}
.items .pop{margin-left:auto;flex:none;font-size:.72rem;font-weight:700;color:var(--pink-text);background:#FDE6F2;border-radius:999px;padding:2px 9px;margin-top:2px}
.items li:target{background:#FFF8E1}
.noresults{padding:24px 0;color:var(--muted)}
.totop{display:none;position:fixed;right:16px;bottom:24px;z-index:14;align-items:center;gap:6px;background:var(--navy);color:#fff;text-decoration:none;font-family:var(--head);font-weight:600;font-size:.88rem;padding:10px 16px;border-radius:999px;box-shadow:0 6px 18px rgba(31,42,92,.3)}
.totop.show{display:inline-flex}
.note{background:var(--soft);border-radius:14px;padding:20px 22px;margin:40px 0 0;color:var(--muted);font-size:.95rem}
.cta{text-align:center;padding:64px 0}
.cta .order>div{justify-content:center}
.ocity-chips{margin-top:18px}
.ocities{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:16px}
.ocity{border:1px solid var(--line);border-radius:16px;padding:18px 18px 20px;scroll-margin-top:calc(var(--hdr) + 16px)}
.ocity:target{border-color:var(--pink);box-shadow:0 0 0 3px #FBD3E7}
.ocity h2{font-size:1.25rem;margin-bottom:12px}
.obtns{display:grid;grid-template-columns:repeat(auto-fit,minmax(0,1fr));gap:10px}
.obtn{white-space:nowrap;font-size:.92rem;text-align:center;text-decoration:none;background:#fff;border:1px solid var(--line);border-radius:12px;padding:11px 10px;font-family:var(--head);font-weight:700;box-shadow:0 4px 0 var(--navy);transition:transform .15s,box-shadow .15s}
.obtn:hover{transform:translateY(2px);box-shadow:0 2px 0 var(--navy)}
.obtn.pick{border-color:var(--navy);box-shadow:0 4px 0 var(--navy),0 0 0 3px #D6DAEA}
footer{background:var(--navy);color:#C9CDE0;padding:44px 0 28px;font-size:.92rem}
footer .wrap{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:28px}
footer .wrap>*{min-width:0}
footer b{display:block;color:#fff;font-family:var(--head);font-weight:600;margin-bottom:8px}
footer a{text-decoration:none;display:block;margin:2px 0}
footer a:hover{color:#fff}
footer .ig{display:inline-flex;align-items:center;gap:8px;margin-top:16px;padding:8px 14px;border:1px solid rgba(255,255,255,.25);border-radius:999px;color:#fff;font-family:var(--head);font-weight:600;font-size:.88rem}
footer .ig:hover{background:rgba(255,255,255,.08)}
footer .ftag{margin:0;max-width:360px}
footer .al{display:block}
footer .about img{height:36px;width:auto;filter:brightness(0) invert(1);margin-bottom:12px}
footer .copy{grid-column:1/-1;border-top:1px solid rgba(255,255,255,.12);padding-top:18px;font-size:.82rem}
@media (max-width:900px){
:root{--hdr:60px}
nav.desk{display:none}
.burger{display:inline-flex}
header .logo img{height:28px}
.hdr-order{margin-left:0}
}
@media (max-width:820px){
.phil .wrap{grid-template-columns:1fr;gap:32px}
.phil img{max-width:260px;aspect-ratio:3/4;object-position:center top}
.logos{grid-template-columns:repeat(3,1fr)}
footer .wrap{grid-template-columns:1fr 1fr}footer .about{grid-column:1/-1}
.loved{grid-template-columns:repeat(2,1fr);gap:12px}.loved p{padding:10px 12px 8px;font-size:.9rem;gap:8px}.loved em{padding:0 12px 12px;font-size:.82rem}.loved .nudge{top:8px;left:8px;font-size:.7rem;padding:4px 9px}
.hero{flex-direction:column;align-items:stretch;min-height:0;padding:22px 0 30px}
.hero::before{display:none}
.hero .wrap,.hero-copy{display:contents}
.hero-copy>*{position:relative;z-index:2}
.hero-copy>.tag{order:1;margin:0 20px 6px}
.hero-copy>h1{order:2;margin:0 20px 0}
.hero img{order:3;position:relative;top:auto;left:auto;z-index:1;width:100%;margin:-12px 0 -16px;height:auto;aspect-ratio:4/3;object-position:58% center;-webkit-mask-image:linear-gradient(180deg,transparent 0,transparent 7%,rgba(0,0,0,.6) 18%,#000 30%,#000 72%,rgba(0,0,0,.6) 84%,transparent 94%,transparent 100%);mask-image:linear-gradient(180deg,transparent 0,transparent 7%,rgba(0,0,0,.6) 18%,#000 30%,#000 72%,rgba(0,0,0,.6) 84%,transparent 94%,transparent 100%)}
.hero-copy>p{order:4;margin:0 20px 16px}
.hero-copy>.order{order:5;margin:0 20px}
}
@media (max-width:820px) and (max-height:700px){.hero img{aspect-ratio:16/10}.hero{padding-top:16px}}
@media (max-width:560px){
section{padding:52px 0}
.order>div{grid-template-columns:repeat(3,1fr);gap:10px}.order a{font-size:.95rem;padding:12px 6px}
.hdr-order{padding:7px 14px}
.hide-xs{display:none}
.cities .grid{grid-template-columns:1fr 1fr;gap:14px 12px}.cities .grid span{font-size:.9rem;padding:11px 10px}
.items{grid-template-columns:1fr}
.logos{grid-template-columns:repeat(2,1fr)}.logos img{height:80px}
}
@media (max-width:560px){
footer{padding:32px 0 calc(20px + env(safe-area-inset-bottom));font-size:.9rem}
footer .wrap{grid-template-columns:1fr;gap:20px}
footer .ftag{display:none}
footer .about{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
footer .about img{margin:0;height:30px}
footer .ig{margin:0}
footer nav b,footer .fcontact b{display:none}
footer nav{display:grid;grid-template-columns:repeat(3,auto);justify-content:start;gap:2px 22px}
footer nav a{margin:0;padding:6px 0;color:#fff;font-family:var(--head);font-weight:500}
footer .fcontact{font-size:.82rem;line-height:1.5}
footer .al{display:inline}footer .al+.al::before{content:" "}
footer .copy{padding-top:14px;font-size:.78rem}
}
@media (max-width:360px){.wrap{padding:0 14px}}
"""

JS = """
(function(){
var d=document;
var b=d.querySelector('.burger'),m=d.getElementById('mnav');
if(b&&m){
  b.setAttribute('role','button');b.setAttribute('aria-expanded','false');b.setAttribute('aria-controls','mnav');
  var set=function(open,kb){m.hidden=!open;b.setAttribute('aria-expanded',open?'true':'false');b.setAttribute('aria-label',open?'Close menu':'Open menu');d.body.classList.toggle('menu-open',open);if(open&&kb){var f=m.querySelector('a');if(f)f.focus();}};
  b.addEventListener('click',function(e){e.preventDefault();set(m.hidden,e.detail===0);});
  b.addEventListener('keydown',function(e){if(e.key===' '){e.preventDefault();set(m.hidden,true);}});
  d.addEventListener('keydown',function(e){if(e.key==='Escape'&&!m.hidden){set(false);b.focus();}});
  m.addEventListener('click',function(e){if(e.target.closest('a'))set(false);});
  window.addEventListener('resize',function(){if(window.innerWidth>900&&!m.hidden)set(false);});
}
var tools=d.querySelector('.mtools');
if(tools){
  tools.hidden=false;
  var q=d.getElementById('q'),veg=d.getElementById('veg'),cnt=d.getElementById('count'),none=d.getElementById('noresults');
  var items=[].slice.call(d.querySelectorAll('.items li')),secs=[].slice.call(d.querySelectorAll('.msec'));
  var run=function(){var t=q.value.trim().toLowerCase(),v=veg.checked,n=0;
    items.forEach(function(li){var ok=(!t||li.getAttribute('data-name').indexOf(t)>-1)&&(!v||li.getAttribute('data-veg')==='1');li.hidden=!ok;if(ok)n++;});
    secs.forEach(function(s){s.hidden=!s.querySelector('li:not([hidden])');});
    none.hidden=n>0;cnt.textContent=(t||v)?(n+(n===1?' dish':' dishes')):'';};
  q.addEventListener('input',run);veg.addEventListener('change',run);
}
var bar=d.querySelector('.chips'),chips=d.querySelectorAll('.chips a[href^="#"]');
if(bar&&chips.length&&'IntersectionObserver' in window){
  var map={};chips.forEach(function(a){map[a.getAttribute('href').slice(1)]=a;});
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(!e.isIntersecting)return;var a=map[e.target.id];if(!a)return;
    chips.forEach(function(c){c.removeAttribute('aria-current');});a.setAttribute('aria-current','true');
    bar.scrollTo({left:Math.max(0,a.offsetLeft-bar.offsetLeft-24),behavior:'smooth'});});},{rootMargin:'-40% 0px -55% 0px'});
  d.querySelectorAll('.msec').forEach(function(s){io.observe(s);});
}
var top=d.querySelector('.totop');
if(top){top.hidden=false;var ft=d.querySelector('footer');var onS=function(){var nearEnd=ft&&ft.getBoundingClientRect().top<window.innerHeight;top.classList.toggle('show',window.scrollY>900&&!nearEnd);};window.addEventListener('scroll',onS,{passive:true});onS();}
var app=(location.search.match(/[?&]app=(swiggy|zomato|ownly)\\b/)||[])[1];
if(app){d.querySelectorAll('.obtn[data-app="'+app+'"]').forEach(function(a){a.classList.add('pick');});}
})();
"""

NAV = (("Home", "./", "index.html"), ("Menu", "menu.html", "menu.html"), ("Blog", "blog.html", "blog.html"),
       ("FAQs", "faq.html", "faq.html"))
CURRENT = ' aria-current="page"'


def url(filename):
    return BASE + "/" + ("" if filename == "index.html" else filename)


def pic(src, alt, w, h, extra=""):
    """<picture> with a WebP source and the JPEG as fallback."""
    webp = src[:-4] + ".webp"
    source = f'<source srcset="{webp}" type="image/webp">' if os.path.exists(os.path.join(ROOT, webp)) else ""
    return f'<picture>{source}<img src="{src}" alt="{escape(alt)}" width="{w}" height="{h}"{extra}></picture>'


def order_boxes():
    boxes = "".join(f'<a href="{escape(ORDER_LINKS[k])}" target="_blank" rel="noopener" style="color:{p["color"]}">{p["label"]}</a>'
                    for k, p in PLATFORMS.items())
    return f'<div class="order" id="order"><span>Order now</span><div>{boxes}</div></div>'


def contact_block():
    rows = ["".join(f'<span class="al">{escape(l)}</span>' for l in ADDRESS)]
    if CONTACT.get("support_email"):
        e = escape(CONTACT["support_email"])
        rows.append(f'<a href="mailto:{e}">{e}</a>')
    if CONTACT.get("phone"):
        p = escape(CONTACT["phone"])
        rows.append(f'<a href="tel:{re.sub(r"[^0-9+]", "", CONTACT["phone"])}">{p}</a>')
    if CONTACT.get("fssai_license"):
        rows.append(f'FSSAI Lic. No. {escape(CONTACT["fssai_license"])}')
    return "<br>".join(rows)


def page(filename, title, description, body, jsonld, noindex=False, extra_head=""):
    canonical = url(filename)
    nav = "".join(
        f'<a href="{href}"{CURRENT if key == filename or (key == "blog.html" and filename.startswith("blog-")) else ""}>{label}</a>'
        for label, href, key in NAV
    )
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>'
                 for j in jsonld)
    robots = '<meta name="robots" content="noindex,nofollow">\n' if (MODE == "review" or noindex) else ""
    share = BASE + "/assets/img/share.jpg"
    return f"""<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
{robots}<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{NAME}">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{share}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{share}">
<meta name="theme-color" content="#1F2A5C">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="preload" href="assets/fonts/poppins-700.woff2" as="font" type="font/woff2" crossorigin>
{extra_head}<link rel="stylesheet" href="assets/style.css">
{ld}
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header><div class="wrap">
<a class="logo" href="./" aria-label="{NAME} home"><img src="assets/img/logo.png" alt="{NAME}" width="119" height="34"></a>
<nav class="desk" aria-label="Main">{nav}<a href="{CUREFOODS}">About Curefoods</a></nav>
<a class="btn sm hdr-order" href="{"#order" if filename in ("index.html", "menu.html") else "./#order"}">Order<span class="hide-xs"> now</span></a>
<a class="burger" href="#footer-nav" aria-label="Open menu"><span></span></a>
</div>
<div id="mnav" class="mnav" hidden><nav aria-label="Mobile">{nav}<a href="{CUREFOODS}">About Curefoods</a></nav></div>
</header>
<main id="main" tabindex="-1">
{body}
</main>
<footer><div class="wrap">
<div class="about"><img src="assets/img/logo.png" alt="{NAME}" width="126" height="36" loading="lazy">
<p class="ftag">{escape(TAGLINE)} {escape(HASHTAG)}</p>
<a class="ig" href="{INSTAGRAM}" target="_blank" rel="noopener"><svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="5" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="17.5" cy="6.5" r="1.2" fill="currentColor"/></svg>Follow @the_eatfit</a></div>
<nav id="footer-nav" aria-label="Footer"><b>Explore</b><a href="./">Home</a><a href="menu.html">Menu</a><a href="blog.html">Blog</a><a href="faq.html">FAQs</a><a href="{CUREFOODS}">About Curefoods</a></nav>
<div class="fcontact"><b>Contact</b>{contact_block()}</div>
<div class="copy">&copy; {date.today().year} {NAME}, a Curefoods brand. All rights reserved.</div>
</div></footer>
<script src="assets/site.js" defer></script>
</body>
</html>
"""


def dot(name):
    v = is_veg(name)
    return f'<span class="dot{"" if v else " nv"}" role="img" aria-label="{"Veg" if v else "Non-veg"}"></span>'


def org_ld():
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": BASE + "/#organization",
        "name": NAME,
        "url": BASE + "/",
        "logo": BASE + "/assets/img/logo.png",
        "parentOrganization": {"@type": "Organization", "name": BRAND["parent"], "url": CUREFOODS},
        "sameAs": BRAND["same_as_verified"],
    }


def restaurant_ld():
    return {
        "@context": "https://schema.org",
        "@type": "Restaurant",
        "name": NAME,
        "url": BASE + "/",
        "logo": BASE + "/assets/img/logo.png",
        "image": BASE + "/assets/img/share.jpg",
        "description": TAGLINE,
        "servesCuisine": ["Indian", "Healthy", "Bowls", "Khichdi", "South Indian"],
        "hasMenu": BASE + "/menu.html",
        "areaServed": CITY_NAMES,
        "parentOrganization": {"@type": "Organization", "name": BRAND["parent"], "url": CUREFOODS},
        "address": {"@type": "PostalAddress", "streetAddress": "No. 72/4, Roopena Agrahara, Hosur Road, Madiwala Post",
                    "addressLocality": "Bengaluru", "addressRegion": "Karnataka", "postalCode": "560068",
                    "addressCountry": "IN"},
        "sameAs": BRAND["same_as_verified"],
    }


def dish_img(item):
    return "assets/img/dish-" + re.sub(r"[^a-z0-9]+", "-", item.lower()).strip("-") + ".jpg"


def dish_id(item):
    return "d-" + slug(tidy(item))


def post_by_slug(s):
    return next(p for p in POSTS if p["slug"] == s)


def trust_strip():
    t = TRUST
    if not all(t.get(k) for k in ("rating", "rating_count", "rating_source", "rating_as_of")):
        return ""
    parts = [f'<span>{escape(str(t["rating"]))} average rating from {escape(str(t["rating_count"]))} ratings '
             f'on {escape(t["rating_source"])} (as of {escape(nice_date(t["rating_as_of"]))})</span>']
    parts += [f'<a href="{escape(p["url"])}" rel="noopener">{escape(p["outlet"])}: {escape(p["title"])}</a>'
              for p in t.get("press", []) if all(p.get(k) for k in ("title", "outlet", "url", "date"))]
    return f'<div class="trust"><div class="wrap">{"".join(parts)}</div></div>'


def build_home(sections):
    # Top sellers that have a dish photo (assets/img/dish-<slug>.jpg, from our Swiggy listing)
    top = sorted(((i, n, t) for t, _, items in sections for i, n in items
                  if os.path.exists(os.path.join(ROOT, dish_img(i)))), key=lambda x: -x[1])[:8]
    cards = []
    for i, _, t in top:
        flag = (f"<!-- PHOTO-FLAG: {escape(PHOTO_FLAGS[tidy(i)])}; replace with real kitchen photography "
                f"(NEEDS-INPUT P1) -->") if tidy(i) in PHOTO_FLAGS else ""
        cards.append(f'{flag}<div class="card">'
                     + (f'<b class="nudge">{escape(NUDGES[tidy(i)])}</b>' if tidy(i) in NUDGES else "")
                     + pic(dish_img(i), tidy(i), 640, 480, ' loading="lazy"')
                     + f'<p>{dot(i)}<span>{escape(tidy(i))}<small>{escape(t)}</small></span></p>'
                     '</div>')
    phil = "".join(f"<h3>{h}</h3><ul>{''.join(f'<li>{x}</li>' for x in pts)}</ul>" for h, pts in PHILOSOPHY)
    p_phil, p_loved = post_by_slug(HOME_POST_LINKS["phil"]), post_by_slug(HOME_POST_LINKS["loved"])
    cities = "".join(f'<span>{escape(c["name"])}</span>' for c in CITIES)
    body = f"""<section class="hero">
{pic("assets/img/bowls.jpg", f"{NAME} healthy bowls", 1200, 600, ' fetchpriority="high"')}
<div class="wrap"><div class="hero-copy">
<span class="tag">{escape(HASHTAG)}</span>
<h1>Healthy food that <span class="accent">tastes like home.</span></h1>
<p>Calorie-counted bowls, khichdi, curries and more. Made with real ingredients, zero trans fat and no deep frying.</p>
{order_boxes()}
</div></div></section>
{trust_strip()}
<section class="phil"><div class="wrap">
{pic("assets/img/tiger.jpg", f"The {NAME} tiger holding a bowl", 664, 900, ' loading="lazy"')}
<div><span class="tag">Our food philosophy</span>
<h2>Eating well shouldn't mean giving up food you love.</h2>
{phil}
<a class="readmore" href="blog-{p_phil["slug"]}.html">Read: {escape(p_phil["title"])} &rarr;</a></div>
</div></section>
<section><div class="wrap">
<span class="tag">Most loved</span>
<h2>What everyone's ordering</h2>
<div class="loved">{"".join(cards)}</div>
<div class="loved-foot"><a class="btn" href="menu.html">See the full menu</a>
<a class="readmore" href="blog-{p_loved["slug"]}.html">Read: {escape(p_loved["title"])} &rarr;</a></div>
</div></section>
<section class="brands"><div class="wrap">
<span class="tag">Our brands</span>
<h2>From the {NAME} kitchens</h2>
<div class="logos">{"".join(f'<img src="assets/img/{f}" alt="{escape(n)}" loading="lazy">' for f, n in BRANDS)}</div>
</div></section>
<div class="cities"><div class="wrap"><span class="tag">Now delivering in</span>
<h2>{len(CITIES)} cities and growing</h2>
<div class="grid">{cities}</div></div></div>"""
    return page("index.html", f"{NAME} | Healthy, calorie-counted food delivered",
                f"{NAME} serves calorie-counted bowls, khichdi, curries and more with zero trans fat. "
                "Order on Swiggy, Zomato or Ownly.", body, [org_ld(), restaurant_ld()],
                extra_head='<link rel="preload" as="image" href="assets/img/bowls.webp" type="image/webp" fetchpriority="high">\n')


def dish_row(item, best):
    name = tidy(item)
    info = DISH.get(name, {})
    desc = f'<span class="ds">{escape(info["description"])}</span>' if info.get("description") else ""
    facts = []
    if info.get("kcal") is not None:
        facts.append(f'{info["kcal"]} kcal')
    if info.get("protein_g") is not None:
        facts.append(f'{info["protein_g"]}g protein')
    if info.get("price_inr") is not None:
        facts.append(f'&#8377;{info["price_inr"]}')
    facts = f'<span class="facts">{" &middot; ".join(facts)}</span>' if facts else ""
    return (f'<li id="{dish_id(item)}" data-name="{escape(name.lower())}" data-veg="{1 if is_veg(item) else 0}">'
            f'{dot(item)}<span><span class="nm">{escape(name)}</span>{desc}{facts}</span>{BEST if best else ""}</li>')


def menu_item_ld(item):
    name = tidy(item)
    it = {"@type": "MenuItem", "name": name}
    if is_veg(item):
        it["suitableForDiet"] = "https://schema.org/VegetarianDiet"
    info = DISH.get(name, {})
    if info.get("description"):
        it["description"] = info["description"]
    nut = {}
    if info.get("kcal") is not None:
        nut["calories"] = f'{info["kcal"]} calories'
    if info.get("protein_g") is not None:
        nut["proteinContent"] = f'{info["protein_g"]} grams'
    if nut:
        it["nutrition"] = {"@type": "NutritionInformation", **nut}
    if info.get("price_inr") is not None:
        it["offers"] = {"@type": "Offer", "price": str(info["price_inr"]), "priceCurrency": "INR"}
    return it


def build_menu(sections):
    chips = "".join(f'<a href="#{slug(t)}">{t}</a>' for t, _, _ in sections)
    secs = []
    for title, note, items in sections:
        lis = "".join(dish_row(i, k < 2 and len(items) > 3) for k, (i, _) in enumerate(items))
        secs.append(f'<section class="msec" id="{slug(title)}" aria-labelledby="h-{slug(title)}"><h2 id="h-{slug(title)}">{title}</h2>'
                    f'<p>{note}</p><ul class="items">{lis}</ul></section>')
    body = f"""<div class="wrap menu-head">
<span class="tag">Menu</span>
<h1>Our menu</h1>
<p>Every dish is calorie-counted and made with zero trans fat. Prices vary by city and app, so check them when you order.</p>
<p class="stamp">Menu updated {nice_date(MENU_DATE)}</p>
{order_boxes()}
</div>
<div class="wrap" id="categories">
<div class="mtools" hidden><input type="search" id="q" placeholder="Search dishes" aria-label="Search dishes" autocomplete="off">
<label class="vegonly"><input type="checkbox" id="veg"> Veg only</label><span class="count" id="count" aria-live="polite"></span></div>
<div class="chips-wrap"><nav class="chips" aria-label="Menu categories">{chips}</nav></div>
{"".join(secs)}
<p class="noresults" id="noresults" hidden>No dishes match. Try a different word or switch off Veg only.</p>
<p class="note"><span class="dot" style="display:inline-block;vertical-align:-2px"></span> Veg &nbsp;&nbsp;
<span class="dot nv" style="display:inline-block;vertical-align:-2px"></span> Non-veg &nbsp;&middot;&nbsp;
Availability can vary by city and kitchen. Seasonal specials (like our Navratri menu) appear on the apps.</p>
</div>
<a class="totop" href="#categories" hidden>Categories &uarr;</a>
<section class="cta"><div class="wrap">
<h2>Hungry?</h2>
{order_boxes()}
</div></section>"""
    menu_ld = {
        "@context": "https://schema.org", "@type": "Menu", "name": f"{NAME} Menu", "url": BASE + "/menu.html",
        "hasMenuSection": [{"@type": "MenuSection", "name": t, "hasMenuItem": [menu_item_ld(i) for i, _ in items]}
                           for t, _, items in sections],
    }
    return page("menu.html", f"Menu | {NAME}",
                f"The full {NAME} menu: fusion bowls, homely bowls, khichdi, curries, curd rice, "
                "breakfast, sugar-free ice cream and drinks.", body, [restaurant_ld(), menu_ld])


BEST = '<span class="pop">Bestseller</span>'


def build_faq():
    faq = "".join(f"<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>" for q, a in FAQ)
    body = f"""<div class="wrap menu-head">
<span class="tag">FAQs</span>
<h1>Frequently asked questions</h1>
<p>Everything you need to know about {NAME}, from our best-sellers to where to order.</p>
</div>
<section class="faq" style="padding-top:8px"><div class="wrap"><div style="max-width:780px">{faq}</div></div></section>"""
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q,
                              "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}
    return page("faq.html", f"FAQs | {NAME}",
                f"Answers about {NAME}: best-selling dishes, cities, where to order, calories, protein, veg and Jain options.",
                body, [faq_ld])


def author_ld():
    return {"@type": "Organization", "name": f"Team {NAME}", "url": BASE + "/"}


LAZY = ' loading="lazy"'


def build_blog():
    cards = "".join(
        f'<a class="post" href="blog-{x["slug"]}.html">{pic(x["image"], x["title"], 640, 360, LAZY)}'
        f'<div><time datetime="{x["date"]}">{nice_date(x["date"])}</time>'
        f'<h3>{escape(x["title"])}</h3><p>{escape(x["summary"])}</p><span>Read more &rarr;</span></div></a>'
        for x in POSTS)
    body = f"""<div class="wrap menu-head">
<span class="tag">Blog</span>
<h1>The {NAME} blog</h1>
<p>Simple ideas for eating well, from the {NAME} kitchen.</p>
</div>
<section style="padding-top:24px"><div class="wrap"><div class="posts">{cards}</div></div></section>"""
    blog_ld = {"@context": "https://schema.org", "@type": "Blog", "name": f"The {NAME} blog", "url": BASE + "/blog.html",
               "blogPost": [{"@type": "BlogPosting", "headline": x["title"], "datePublished": x["date"],
                             "image": f"{BASE}/{x['image']}", "author": author_ld(),
                             "url": f"{BASE}/blog-{x['slug']}.html"} for x in POSTS]}
    return page("blog.html", f"Blog | {NAME}", f"Simple ideas for eating well, from the {NAME} kitchen.", body, [blog_ld])


def link_dishes(text_html, dishes):
    """Link the first mention of each menu dish in an (already escaped) paragraph."""
    for name, target in dishes:
        esc = escape(name)
        pos = text_html.find(esc)
        if pos == -1 or text_html.rfind("<a ", 0, pos) > text_html.rfind("</a>", 0, pos):
            continue
        text_html = text_html[:pos] + f'<a href="menu.html#{target}">{esc}</a>' + text_html[pos + len(esc):]
    return text_html


def build_post(x, sections):
    dishes = sorted(((tidy(i), dish_id(i)) for _, _, items in sections for i, _ in items), key=lambda d: -len(d[0]))
    paras = "".join(f"<h2>{escape(t[3:])}</h2>" if t.startswith("## ") else f"<p>{link_dishes(escape(t), dishes)}</p>"
                    for t in x["body"])
    others = "".join(f'<li><a href="blog-{o["slug"]}.html">{escape(o["title"])}</a></li>' for o in POSTS if o is not x)
    body = f"""<article class="wrap article">
<nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="./">Home</a></li><li><a href="blog.html">Blog</a></li><li aria-current="page">{escape(x["title"])}</li></ol></nav>
<time datetime="{x["date"]}">{nice_date(x["date"])} &middot; Team {NAME}</time>
<h1>{escape(x["title"])}</h1>
{pic(x["image"], x["title"], 640, 360, ' class="cover"')}
{paras}
<div class="note"><b>Hungry?</b> order {NAME} on <a href="./#order">Swiggy, Zomato or Ownly</a>, or <a href="menu.html">see the full menu</a>.</div>
<h3 style="margin-top:40px">More from the blog</h3><ul class="more">{others}</ul>
</article>"""
    post_url = f"{BASE}/blog-{x['slug']}.html"
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": x["title"], "description": x["summary"],
          "datePublished": x["date"], "dateModified": x["date"], "image": f"{BASE}/{x['image']}", "author": author_ld(),
          "publisher": {"@type": "Organization", "name": NAME, "logo": {"@type": "ImageObject", "url": BASE + "/assets/img/logo.png"}},
          "mainEntityOfPage": post_url}
    crumbs = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Blog", "item": BASE + "/blog.html"},
        {"@type": "ListItem", "position": 3, "name": x["title"], "item": post_url}]}
    return page(f"blog-{x['slug']}.html", f"{x['title']} | {NAME} blog", x["summary"], body, [ld, crumbs])


NOT_FOUND = """<section><div class="wrap" style="text-align:center">
<h1>Page not found</h1><p>That page has moved or doesn't exist.</p>
<a class="btn" href="./">Back to home</a></div></section>"""

PAGES = ["index.html", "menu.html", "faq.html", "blog.html"] + [f"blog-{x['slug']}.html" for x in POSTS]

AI_TRAINING = ["GPTBot", "ClaudeBot", "anthropic-ai", "Google-Extended", "Applebot-Extended", "CCBot",
               "Meta-ExternalAgent", "Amazonbot"]
AI_RETRIEVAL = ["OAI-SearchBot", "ChatGPT-User", "PerplexityBot", "Perplexity-User", "Claude-SearchBot",
                "Claude-User", "DuckAssistBot", "MistralAI-User"]


def build_robots():
    train_rule = "Allow: /" if AI_POLICY == "allow-all" else "Disallow: /"
    retrieval = ("# (block-training: retrieval crawlers fall under the User-agent: * rule above)\n"
                 if AI_POLICY == "block-training" else
                 "".join(f"User-agent: {b}\n" for b in AI_RETRIEVAL) + "Allow: /\n")
    return f"""# Generated by build/generate.py from site.config.json (robots_ai_policy: {AI_POLICY}).
# These rules express crawl permission only. They do not cause indexing or citation.
User-agent: *
Allow: /

# Group 1: AI retrieval / search crawlers. They fetch pages to answer a user's
# question or to build an AI search index.
{retrieval}
# Group 2: AI training crawlers. They collect content for model training.
{"".join(f"User-agent: {b}{chr(10)}" for b in AI_TRAINING)}{train_rule}

# LLM-readable summaries: {BASE}/llms.txt and {BASE}/llms-full.txt

Sitemap: {BASE}/sitemap.xml
"""


def build_sitemap():
    lastmod = {"menu.html": MENU_DATE, **{f"blog-{x['slug']}.html": x["date"] for x in POSTS}}
    rows = "".join(f"<url><loc>{url(p)}</loc>" + (f"<lastmod>{lastmod[p]}</lastmod>" if p in lastmod else "") + "</url>"
                   for p in PAGES)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{rows}</urlset>\n')


def build_llms(sections):
    menu = "\n".join(f"- {t}: " + "; ".join(tidy(i) for i, _ in items) for t, _, items in sections)
    phil = "; ".join(x for _, pts in PHILOSOPHY for x in pts)
    faq = "\n".join(f"- {q} {a}" for q, a in FAQ)
    order = "\n".join(f"- {c['name']}: " + ", ".join(f"{PLATFORMS[k]['label']} ({c['order'][k]})"
                                                    for k in PLATFORMS if c["order"].get(k)) for c in CITIES)
    posts = "\n".join(f"  - [{x['title']}]({BASE}/blog-{x['slug']}.html): {x['summary']}" for x in POSTS)
    llms = f"""# {NAME}

> {TAGLINE} A Curefoods brand. {HASHTAG}

- Parent company: Curefoods India Ltd. ({CUREFOODS})
- Address: {" ".join(ADDRESS)}
- Cities: {", ".join(CITY_NAMES)}
- Order: Swiggy ({ORDER_LINKS["swiggy"]}), Zomato ({ORDER_LINKS["zomato"]}), Ownly app ({ORDER_LINKS["ownly"]})
- Instagram: {INSTAGRAM}
- Kitchen brands: {", ".join(n for _, n in BRANDS)}
- Food philosophy: {phil}
- Prices vary by city and app; see the ordering apps for current prices.

## Menu (updated {MENU_DATE})
{menu}

## Order links by city
{order}

## FAQ
{faq}

## Pages
- [Home]({BASE}/)
- [Menu]({BASE}/menu.html)
- [FAQs]({BASE}/faq.html)
- [Blog]({BASE}/blog.html)
{posts}
"""
    bodies = "\n\n".join(f"### {x['title']}\n{BASE}/blog-{x['slug']}.html\n\n" + "\n\n".join(
        ("#### " + t[3:]) if t.startswith("## ") else t for t in x["body"]) for x in POSTS)
    full = llms.replace("## Pages", f"## Blog posts\n\n{bodies}\n\n## Pages")
    return llms, full


def write(name, content):
    os.makedirs(os.path.dirname(os.path.join(OUT, name)), exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    sections = load_menu()
    write("assets/style.css", CSS.strip() + "\n")
    write("assets/site.js", JS.strip() + "\n")
    write("index.html", build_home(sections))
    write("menu.html", build_menu(sections))
    write("faq.html", build_faq())
    write("blog.html", build_blog())
    for x in POSTS:
        write(f"blog-{x['slug']}.html", build_post(x, sections))
    write("404.html", page("404.html", f"Not found | {NAME}", TAGLINE, NOT_FOUND, [], noindex=True))
    write("robots.txt", build_robots())
    write("sitemap.xml", build_sitemap())
    llms, full = build_llms(sections)
    write("llms.txt", llms)
    write("llms-full.txt", full)
    write(".nojekyll", "")
    n = sum(len(items) for _, _, items in sections)
    print(f"Built {len(PAGES) + 1} pages ({len(sections)} menu sections, {n} dishes), mode={MODE}, base={BASE}, ai={AI_POLICY}")
