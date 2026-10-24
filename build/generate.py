"""Builds the simple 2-page Eatfit site (Home + Menu).

Menu comes from build/menu_live.tsv (category, item, units sold in the last
7 days, pulled from ClickHouse). Re-pull that file and run:
    python3 build/generate.py
"""
import csv
import re
import json
import os
from datetime import date
from html import escape

from posts import POSTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = "https://www.eatfit.in"
TODAY = date.today().isoformat()

ORDER = {
    "Swiggy": "https://www.swiggy.com/direct/brand/76139?source=swiggy-direct&subSource=generic",
    "Zomato": "https://link.zomato.com/xqzv/rx68ggmv",
    "Ownly": "https://ownly.food/app/brand/BR112474",
}
CUREFOODS_ABOUT = "https://curefoods.in/"
INSTAGRAM = "https://www.instagram.com/the_eatfit"
BRANDS = [
    ("brand-eatfit.png", "Eatfit"),
    ("brand-gik.png", "Great Indian Khichdi"),
    ("brand-rolls.png", "Rolls on Wheels"),
    ("brand-mcrc.png", "Madras Curd Rice Company"),
    ("brand-millet.png", "Millet Express"),
]
CITIES = ["Bengaluru", "Delhi NCR", "Hyderabad", "Mumbai", "Pune", "Chandigarh", "Chennai", "Coimbatore"]
ADDRESS = ["Curefoods India Ltd.", "No. 72/4, Roopena Agrahara,", "Hosur Road, Madiwala Post,",
           "Bengaluru, Karnataka 560068"]
TAGLINE = ("Healthy, yummy, honest and wholesome Indian food, made with real ingredients, "
           "zero trans fat and lots of love.")

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

PHILOSOPHY = [
    ("Better processes", ["ISO-certified kitchens", "Farm-to-fork tracking",
                          "Calorie counted", "Nutritionist approved"]),
    ("Better ingredients", ["Zero trans fats", "Zero chemicals",
                            "Whole grains", "Zero deep frying"]),
]
FAQ = [
    ("What is Eatfit?",
     "Eatfit, by Curefoods, serves honest, clean and tasty Indian and global comfort meals made "
     "with healthy ingredients and no preservatives."),
    ("What are Eatfit's most popular dishes?",
     "Classic Rajma Chawal, Homely Vegetable Khichdi, Creamy Pesto Paneer Bowl, Quinoa Khichdi and "
     "Classic Curd Rice. Khichdi is our most-ordered category."),
    ("Which cities is Eatfit available in?",
     ", ".join(CITIES[:-1]) + " and " + CITIES[-1] + "."),
    ("Where can I order Eatfit online?",
     "On Swiggy, Zomato and Ownly. Search for \"Eatfit\" in the app."),
    ("What is the most popular Eatfit dish in my city?",
     "Rajma Chawal in Delhi NCR, Chandigarh and Coimbatore; Vegetable Khichdi in Bengaluru and Pune; "
     "Quinoa Khichdi in Hyderabad; Curd Rice in Mumbai; Pesto Paneer Bowl in Chennai."),
    ("What should I order for a healthy lunch?",
     "Lunch is our busiest meal. Top picks: Rajma Chawal, Dal Tadka Chawal and the Creamy Pesto Paneer Bowl."),
    ("What is a good light dinner option?",
     "Khichdi is our top dinner pick. Try Homely Vegetable, Quinoa or Simple Dal Khichdi."),
    ("Is Eatfit food calorie-counted?",
     "Yes, and nutritionist-approved. Nutrition details are on each dish in the ordering app."),
    ("Is Eatfit good if I'm watching my weight?",
     "Our meals are portion-controlled and never deep fried, which makes them an easy everyday choice."),
    ("Does Eatfit have high-protein meals?",
     "Yes. Paneer, chicken and soya chaap bowls, rajma and chana meals, and Protein Milkshakes with 25g protein."),
    ("Are there vegetarian and Jain options?",
     "Most of the menu is vegetarian. Our Jain khichdis are made without onion or garlic."),
    ("Does Eatfit serve South Indian food?",
     "Yes. A full curd rice range, plus all-day Masala Dosa, Idli and Vada."),
    ("Does Eatfit have healthy desserts?",
     "Yes. Sugar-free ice creams and kulfis."),
    ("Does Eatfit use preservatives or deep frying?",
     "No. Zero deep frying, zero trans fats and zero chemicals."),
    ("Is Eatfit part of Curefoods?",
     "Yes. Eatfit is a Curefoods brand."),
]


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
    return s.lower().replace(" & ", "-").replace(" ", "-")


CSS = """
:root{--navy:#1F2A5C;--pink:#E4007C;--pink-dark:#B80064;--teal:#17A2B4;--teal-tint:#E3F5F7;
--plum:#962B7F;--ink:#1F2A5C;--muted:#5A6079;--bg:#FFFFFF;--soft:#F5F6FA;--line:#E3E5EE;
--veg:#1E8E3E;--nonveg:#B3261E;
--head:"Poppins",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
--body:"Nunito Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
*,*::before,*::after{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 var(--body);-webkit-font-smoothing:antialiased}
img{max-width:100%;display:block}
a{color:inherit}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px}
h1,h2,h3{font-family:var(--head);line-height:1.15;margin:0 0 .45em;color:var(--navy)}
h1{font-size:clamp(2.1rem,5.5vw,3.5rem);font-weight:700}
h2{font-size:clamp(1.6rem,3.6vw,2.3rem);font-weight:700}
h3{font-size:1.15rem;font-weight:600}
.accent{color:var(--pink)}
header{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}
header .wrap{display:flex;align-items:center;justify-content:space-between;height:64px;gap:12px}
header img{height:34px;width:auto}
nav{display:flex;align-items:center;gap:20px}
nav a{text-decoration:none;font-family:var(--head);font-weight:500;font-size:.95rem}
nav a[aria-current]{color:var(--pink)}
.btn{display:inline-block;background:var(--pink);color:#fff;text-decoration:none;font-family:var(--head);
font-weight:600;font-size:.95rem;padding:11px 22px;border-radius:999px;border:2px solid var(--pink);transition:background .15s}
.btn:hover{background:var(--pink-dark);border-color:var(--pink-dark)}
.btn.ghost{background:#fff;color:var(--navy);border-color:var(--line)}
.btn.ghost:hover{border-color:var(--navy);background:#fff}
.btn.sm{padding:7px 16px;font-size:.85rem}
.btns{display:flex;flex-wrap:wrap;gap:10px}
.order>span{display:block;font-family:var(--head);font-weight:700;font-size:.82rem;letter-spacing:.14em;text-transform:uppercase;color:var(--navy);margin-bottom:10px}
.order>div{display:grid;grid-template-columns:repeat(3,minmax(0,150px));gap:12px}
.order a{display:block;text-align:center;text-decoration:none;background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 10px;
font-family:var(--head);font-weight:700;font-size:1.05rem;box-shadow:0 5px 0 var(--navy),0 10px 18px rgba(31,42,92,.15);transition:transform .15s,box-shadow .15s}
.order a:hover{transform:translateY(3px);box-shadow:0 2px 0 var(--navy),0 5px 10px rgba(31,42,92,.15)}
.menu-head .order{margin-top:18px}
@media (max-width:560px){.order>div{grid-template-columns:repeat(3,1fr);gap:10px}.order a{font-size:.95rem;padding:12px 6px}.hide-sm{display:none}}
section{padding:72px 0}
.hero{position:relative;padding:0;min-height:min(640px,78vh);display:flex;align-items:center;overflow:hidden;background:#fff}
.hero>img{position:absolute;top:0;left:12%;width:100%;height:100%;object-fit:cover;object-position:center;-webkit-mask-image:linear-gradient(90deg,transparent 0,#000 30%);mask-image:linear-gradient(90deg,transparent 0,#000 30%)}
.hero::before{content:"";position:absolute;inset:0;z-index:1;
background:linear-gradient(90deg,rgba(255,255,255,.97) 0,rgba(255,255,255,.9) 34%,rgba(255,255,255,0) 62%)}
.hero .wrap{position:relative;z-index:2;width:100%;padding-top:64px;padding-bottom:64px}
.hero-copy{max-width:600px}
.hero p{font-size:1.15rem;color:var(--muted);max-width:500px;margin:0 0 28px}
.tag{display:inline-block;font-family:var(--head);font-weight:600;font-size:.8rem;letter-spacing:.08em;
text-transform:uppercase;color:var(--teal);margin-bottom:12px}
.phil{background:#FFF1F7;color:var(--navy)}
.phil .wrap{display:grid;grid-template-columns:1fr 1.3fr;gap:48px;align-items:center}
.phil img{border-radius:20px;width:100%;height:auto;max-width:340px;aspect-ratio:1/1;object-fit:cover;object-position:center 30%;margin:0 auto}
.phil h2{color:var(--navy)}
.phil h3{color:var(--pink);margin-top:24px}
.phil ul{list-style:none;padding:0;margin:0;display:grid;grid-template-columns:1fr 1fr;gap:10px}
.phil li{background:#fff;border:1px solid #F6D3E3;box-shadow:0 1px 2px rgba(31,42,92,.05);border-radius:12px;padding:12px 14px;font-weight:600;font-size:.95rem}
.phil li::before{content:"\\2713";color:var(--teal);font-weight:800;margin-right:8px}
.loved{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:24px 0 32px}
.loved a{position:relative;display:flex;flex-direction:column;text-decoration:none;color:inherit;border:1px solid var(--line);border-radius:16px;overflow:hidden;background:#fff;transition:transform .15s,box-shadow .15s}
.loved .nudge{position:absolute;top:12px;left:12px;background:var(--pink);color:#fff;font-family:var(--head);font-weight:600;font-size:.78rem;padding:5px 11px;border-radius:999px;box-shadow:0 2px 8px rgba(0,0,0,.18)}
.loved em{font-style:normal;font-family:var(--head);font-weight:600;font-size:.88rem;color:var(--pink);padding:0 16px 16px;margin-top:auto}
.loved a:hover em{text-decoration:underline}
.loved a:hover{transform:translateY(-3px);box-shadow:0 12px 28px rgba(31,42,92,.10)}
.loved img{width:100%;height:auto;aspect-ratio:4/3;object-fit:cover}
.loved p{display:flex;gap:10px;align-items:flex-start;margin:0;padding:14px 16px 16px;font-weight:600;line-height:1.35}
.loved small{display:block;font-weight:400;color:var(--muted)}
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
.post time,.article time{font-size:.82rem;color:var(--teal);font-weight:700}
.post h3{margin:8px 0 6px;font-size:1.2rem}
.post p{color:var(--muted);flex:1;margin:0 0 14px}
.post span{color:var(--pink);font-weight:700;font-size:.9rem}
.article{max-width:740px;padding-top:40px;padding-bottom:64px}
.article h1{font-size:clamp(1.8rem,4.5vw,2.6rem);margin-top:8px}
.article h2{font-size:1.35rem;margin:30px 0 8px}
.article p{font-size:1.06rem;color:#3A4160}
.article .note a{color:var(--pink);font-weight:700}
.back{display:block;width:max-content;text-decoration:none;color:var(--muted);font-size:.9rem;margin-bottom:18px}
.more{padding-left:18px}.more a{color:var(--pink)}
.cities{background:linear-gradient(135deg,var(--pink),#B80064);padding:56px 0 64px;text-align:center}
.cities .tag{color:#FFD3E8}
.cities h2{color:#fff;margin:6px 0 28px}
.cities .grid{display:grid;grid-template-columns:repeat(4,minmax(0,190px));justify-content:center;gap:18px 16px}
.cities .grid span{display:inline-block;background:#fff;color:var(--navy);font-family:var(--head);font-weight:700;font-size:1.02rem;padding:14px 22px;border-radius:14px;
box-shadow:0 6px 0 var(--navy),0 14px 24px rgba(31,42,92,.35);transform:perspective(500px) rotateX(8deg);transition:transform .15s,box-shadow .15s}
.cities .grid span:hover{transform:perspective(500px) rotateX(0) translateY(4px);box-shadow:0 2px 0 var(--navy),0 6px 12px rgba(31,42,92,.3)}
@media (max-width:560px){.cities .grid{grid-template-columns:1fr 1fr;gap:14px 12px}.cities .grid span{font-size:.9rem;padding:11px 16px}}
.faq details{border-bottom:1px solid var(--line);padding:16px 0}
.faq summary{cursor:pointer;font-family:var(--head);font-weight:600;list-style:none;display:flex;justify-content:space-between;gap:16px}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";color:var(--pink);font-size:1.3rem;line-height:1}
.faq details[open] summary::after{content:"\\2212"}
.faq p{margin:10px 0 0;color:var(--muted)}
.menu-head{padding-top:48px;padding-bottom:8px}
.menu-head p{color:var(--muted);max-width:620px}
.chips{display:flex;gap:8px;overflow-x:auto;padding:14px 0;position:sticky;top:64px;background:#fff;z-index:5;
border-bottom:1px solid var(--line);scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chips a{flex:none;text-decoration:none;font-family:var(--head);font-size:.85rem;font-weight:500;padding:7px 14px;
border:1px solid var(--line);border-radius:999px;white-space:nowrap}
.chips a:hover{border-color:var(--pink);color:var(--pink)}
.msec{padding:40px 0 8px;scroll-margin-top:130px}
.msec>p{color:var(--muted);margin:-4px 0 18px}
.items{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:0 32px;list-style:none;padding:0;margin:0}
.items li{display:flex;gap:12px;align-items:flex-start;padding:12px 0;border-bottom:1px solid var(--line)}
.items .pop{margin-left:auto;flex:none;font-size:.72rem;font-weight:700;color:var(--pink);background:#FDE6F2;border-radius:999px;padding:2px 9px;margin-top:2px}
.note{background:var(--soft);border-radius:14px;padding:20px 22px;margin:40px 0 0;color:var(--muted);font-size:.95rem}
.cta{text-align:center;padding:64px 0}
.cta .btns{justify-content:center}
footer{background:var(--navy);color:#C9CDE0;padding:44px 0 28px;font-size:.92rem}
footer .wrap{display:grid;grid-template-columns:1.4fr 1fr 1fr;gap:28px}
footer b{display:block;color:#fff;font-family:var(--head);font-weight:600;margin-bottom:8px}
footer a{text-decoration:none;display:block;margin:2px 0}
footer a:hover{color:#fff}
footer img{height:36px;width:auto;filter:brightness(0) invert(1);margin-bottom:12px}
footer .copy{grid-column:1/-1;border-top:1px solid rgba(255,255,255,.12);padding-top:18px;font-size:.82rem}
@media (max-width:820px){
.phil .wrap{grid-template-columns:1fr;gap:32px}
.loved{grid-template-columns:repeat(2,1fr);gap:12px}.loved p{padding:10px 12px 8px;font-size:.9rem;gap:8px}.loved em{padding:0 12px 12px;font-size:.82rem}.loved .nudge{top:8px;left:8px;font-size:.7rem;padding:4px 9px}
.hero{min-height:calc(100svh - 96px);align-items:flex-end}
.hero>img{left:0;height:68%;object-position:58% center;-webkit-mask-image:none;mask-image:none}
.hero::before{background:linear-gradient(0deg,#fff 0,#fff 34%,rgba(255,255,255,.85) 46%,rgba(255,255,255,0) 64%)}
.hero .wrap{padding-top:0;padding-bottom:28px}
.phil img{max-width:240px}
.logos{grid-template-columns:repeat(3,1fr)}
footer .wrap{grid-template-columns:1fr 1fr}footer .about{grid-column:1/-1}}
@media (max-width:560px){
section{padding:52px 0}
header .wrap{flex-wrap:wrap;height:auto;padding:10px 12px 8px;gap:8px}header img{height:26px}nav{width:100%;display:flex;gap:5px}nav a{flex:1 1 auto;text-align:center;white-space:nowrap;font-size:clamp(.68rem,3.3vw,.8rem);padding:7px 4px;border-radius:999px;background:var(--soft,#F4F5FA);border:1px solid var(--line)}nav a[aria-current]{background:var(--pink);color:#fff;border-color:var(--pink)}nav .btn{display:none}

.items{grid-template-columns:1fr}
.logos{grid-template-columns:repeat(2,1fr)}.logos img{height:80px}}
"""


APP_COLORS = {"Swiggy": "#FC8019", "Zomato": "#E23744", "Ownly": "#1F2A5C"}


def order_boxes():
    boxes = "".join(f'<a href="{url}" target="_blank" rel="noopener" style="color:{APP_COLORS[name]}">{name}</a>'
                    for name, url in ORDER.items())
    return f'<div class="order"><span>Order now</span><div>{boxes}</div></div>'


def page(filename, title, description, body, jsonld):
    canonical = DOMAIN + "/" + ("" if filename == "index.html" else filename)
    links = (("Home", "./", "index.html"), ("Menu", "menu.html", "menu.html"), ("Blog", "blog.html", "blog.html"), ("FAQs", "faq.html", "faq.html"))
    nav = "".join(
        f'<a href="{href}"{CURRENT if key == filename or (key == "blog.html" and filename.startswith("blog-")) else ""}>{label}</a>'
        for label, href, key in links
    )
    ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>'
                 for j in jsonld)
    return f"""<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Eatfit">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{DOMAIN}/assets/img/bowls.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#1F2A5C">
<link rel="icon" href="assets/img/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700&family=Nunito+Sans:wght@400;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
{ld}
</head>
<body>
<header><div class="wrap">
<a href="./" aria-label="Eatfit home"><img src="assets/img/logo.png" alt="Eatfit" width="119" height="34"></a>
<nav>{nav}<a href="{CUREFOODS_ABOUT}">About Curefoods</a><a class="btn sm" href="{ORDER["Swiggy"]}" target="_blank" rel="noopener">Order now</a></nav>
</div></header>
<main>
{body}
</main>
<footer><div class="wrap">
<div class="about"><img src="assets/img/logo.png" alt="Eatfit" width="126" height="36">
<p style="margin:0;max-width:360px">{escape(TAGLINE)} #HealthyMadeHappier</p></div>
<div><b>Explore</b><a href="./">Home</a><a href="menu.html">Menu</a><a href="blog.html">Blog</a><a href="faq.html">FAQs</a><a href="{CUREFOODS_ABOUT}">About Curefoods</a><a href="{INSTAGRAM}" target="_blank" rel="noopener">Instagram</a></div>
<div><b>Contact</b>{"<br>".join(escape(l) for l in ADDRESS)}</div>
<div class="copy">&copy; {date.today().year} Eatfit, a Curefoods brand. All rights reserved.</div>
</div></footer>
</body>
</html>
"""


CURRENT = ' aria-current="page"'


def dot(name):
    return f'<span class="dot{"" if is_veg(name) else " nv"}" aria-label="{"Veg" if is_veg(name) else "Non-veg"}"></span>'


def org_ld():
    return {
        "@context": "https://schema.org",
        "@type": "Restaurant",
        "name": "Eatfit",
        "url": DOMAIN,
        "logo": DOMAIN + "/assets/img/logo.png",
        "image": DOMAIN + "/assets/img/bowls.jpg",
        "description": TAGLINE,
        "servesCuisine": ["Indian", "Healthy", "Bowls", "Khichdi", "South Indian"],
        "hasMenu": DOMAIN + "/menu.html",
        "areaServed": CITIES,
        "parentOrganization": {"@type": "Organization", "name": "Curefoods", "url": "https://curefoods.in"},
        "sameAs": [INSTAGRAM, ORDER["Swiggy"], ORDER["Zomato"], ORDER["Ownly"]],
        "address": {"@type": "PostalAddress", "streetAddress": "No. 72/4, Roopena Agrahara, Hosur Road, Madiwala Post",
                    "addressLocality": "Bengaluru", "addressRegion": "Karnataka", "postalCode": "560068",
                    "addressCountry": "IN"},
        "sameAs": [INSTAGRAM],
    }


def dish_img(item):
    return "assets/img/dish-" + re.sub(r"[^a-z0-9]+", "-", item.lower()).strip("-") + ".jpg"


# Short nudges on the Most Loved cards (directional, from order data)
NUDGES = {
    "Creamy Pesto Paneer Bowl": "#1 Fusion Bowl",
    "Desi Dal Tadka Chawal": "Comfort classic",
    "Classic Curd Rice": "Mumbai's favourite",
    "Lasooni Methi Paneer with Steam Rice": "Protein-packed",
    "Dal Makhani Chawal": "Rich & creamy",
    "Homely Vegetable Khichdi": "#1 in Bengaluru",
    "Black Chana with Steamed Rice": "High fibre",
    "Cheesy Peri Peri Paneer Bowl": "Spicy pick",
}


def build_home(sections):
    # Top sellers that have a dish photo (assets/img/dish-<slug>.jpg, from our Swiggy listing)
    top = sorted(((i, n, t) for t, _, items in sections for i, n in items
                  if os.path.exists(os.path.join(ROOT, dish_img(i)))), key=lambda x: -x[1])[:8]
    loved = "".join(f'<a href="{ORDER["Swiggy"]}" target="_blank" rel="noopener">'
                    + (f'<b class="nudge">{escape(NUDGES[tidy(i)])}</b>' if tidy(i) in NUDGES else "")
                    + f'<img src="{dish_img(i)}" alt="{escape(tidy(i))}" width="640" height="480" loading="lazy">'
                    f'<p>{dot(i)}<span>{escape(tidy(i))}<small>{escape(t)}</small></span></p>'
                    f'<em>Order now &rarr;</em></a>'
                    for i, _, t in top)
    phil = "".join(f"<h3>{h}</h3><ul>{''.join(f'<li>{x}</li>' for x in pts)}</ul>" for h, pts in PHILOSOPHY)
    body = f"""<section class="hero">
<img src="assets/img/bowls.jpg" alt="Eatfit healthy bowls" width="1200" height="600">
<div class="wrap"><div class="hero-copy">
<span class="tag">#HealthyMadeHappier</span>
<h1>Healthy food that <span class="accent">tastes like home.</span></h1>
<p>Calorie-counted bowls, khichdi, curries and more. Made with real ingredients, zero trans fat and no deep frying.</p>
{order_boxes()}
</div></div></section>
<section class="phil"><div class="wrap">
<img src="assets/img/tiger.jpg" alt="The Eatfit tiger holding a bowl" width="664" height="900" loading="lazy">
<div><span class="tag">Our food philosophy</span>
<h2>Eating well shouldn't mean giving up food you love.</h2>
{phil}</div>
</div></section>
<section><div class="wrap">
<span class="tag">Most loved</span>
<h2>What everyone's ordering</h2>
<div class="loved">{loved}</div>
<a class="btn" href="menu.html">See the full menu</a>
</div></section>
<section class="brands"><div class="wrap">
<span class="tag">Our brands</span>
<h2>From the Eatfit kitchens</h2>
<div class="logos">{"".join(f'<img src="assets/img/{f}" alt="{escape(n)}" loading="lazy">' for f, n in BRANDS)}</div>
</div></section>
<div class="cities"><div class="wrap"><span class="tag">Now delivering in</span>
<h2>{len(CITIES)} cities and growing</h2>
<div class="grid">{"".join(f"<span>{c}</span>" for c in CITIES)}</div></div></div>"""
    return page("index.html", "Eatfit | Healthy, calorie-counted food delivered",
                "Eatfit serves calorie-counted bowls, khichdi, curries and more with zero trans fat. "
                "Order on Swiggy, Zomato or Ownly.", body, [org_ld()])


def build_menu(sections):
    chips = "".join(f'<a href="#{slug(t)}">{t}</a>' for t, _, _ in sections)
    secs = []
    for title, note, items in sections:
        lis = "".join(
            f"<li>{dot(i)}<span>{escape(tidy(i))}</span>{BEST if k < 2 and len(items) > 3 else ''}</li>"
            for k, (i, _) in enumerate(items)
        )
        secs.append(f'<div class="msec" id="{slug(title)}"><h2>{title}</h2><p>{note}</p><ul class="items">{lis}</ul></div>')
    body = f"""<div class="wrap menu-head">
<span class="tag">Menu</span>
<h1>Our menu</h1>
<p>Every dish is calorie-counted and made with zero trans fat. Prices vary by city and app, so check them when you order.</p>
{order_boxes()}
</div>
<div class="wrap"><div class="chips">{chips}</div>
{"".join(secs)}
<p class="note"><span class="dot" style="display:inline-block;vertical-align:-2px"></span> Veg &nbsp;&nbsp;
<span class="dot nv" style="display:inline-block;vertical-align:-2px"></span> Non-veg &nbsp;&middot;&nbsp;
Availability can vary by city and kitchen. Seasonal specials (like our Navratri menu) appear on the apps.</p>
</div>
<section class="cta"><div class="wrap">
<h2>Hungry?</h2>
{order_boxes()}
</div></section>"""
    menu_ld = {
        "@context": "https://schema.org", "@type": "Menu", "name": "Eatfit Menu", "url": DOMAIN + "/menu.html",
        "hasMenuSection": [{"@type": "MenuSection", "name": t,
                            "hasMenuItem": [{"@type": "MenuItem", "name": tidy(i),
                                             "suitableForDiet": "https://schema.org/VegetarianDiet" if is_veg(i) else None}
                                            for i, _ in items]}
                           for t, _, items in sections],
    }
    for s in menu_ld["hasMenuSection"]:
        for it in s["hasMenuItem"]:
            if it["suitableForDiet"] is None:
                del it["suitableForDiet"]
    return page("menu.html", "Menu | Eatfit",
                "The full Eatfit menu: fusion bowls, homely bowls, khichdi, curries, curd rice, "
                "breakfast, sugar-free ice cream and drinks.", body, [org_ld(), menu_ld])


BEST = '<span class="pop">Bestseller</span>'


def build_seo(sections):
    robots = f"""User-agent: *
Allow: /

# AI / answer-engine crawlers welcome
User-agent: GPTBot
Allow: /
User-agent: ChatGPT-User
Allow: /
User-agent: PerplexityBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: Perplexity-User
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: Claude-User
Allow: /
User-agent: anthropic-ai
Allow: /
User-agent: Applebot
Allow: /
User-agent: Applebot-Extended
Allow: /
User-agent: Googlebot
Allow: /
User-agent: Bingbot
Allow: /
User-agent: DuckAssistBot
Allow: /
User-agent: Meta-ExternalAgent
Allow: /
User-agent: Amazonbot
Allow: /
User-agent: MistralAI-User
Allow: /
User-agent: CCBot
Allow: /

# LLM-readable summaries: {DOMAIN}/llms.txt and {DOMAIN}/llms-full.txt

Sitemap: {DOMAIN}/sitemap.xml
"""
    urls = "".join(f"<url><loc>{DOMAIN}/{p}</loc><lastmod>{TODAY}</lastmod></url>" for p in ["", "menu.html", "faq.html", "blog.html"] + [f"blog-{x['slug']}.html" for x in POSTS])
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    menu = "\n".join(f"- {t}: " + "; ".join(tidy(i) for i, _ in items) for t, _, items in sections)
    phil = "; ".join(x for _, pts in PHILOSOPHY for x in pts)
    faq = "\n".join(f"- {q} {a}" for q, a in FAQ)
    llms = f"""# Eatfit

> {TAGLINE} A Curefoods brand. #HealthyMadeHappier

- Parent company: Curefoods India Ltd. (https://curefoods.in)
- Address: {" ".join(ADDRESS)}
- Cities: {", ".join(CITIES)}
- Order: Swiggy ({ORDER["Swiggy"]}), Zomato ({ORDER["Zomato"]}), Ownly ({ORDER["Ownly"]})
- Instagram: {INSTAGRAM}
- Kitchen brands: {", ".join(n for _, n in BRANDS)}
- Food philosophy: {phil}
- Prices vary by city and app; see the ordering apps for current prices.

## Menu (as of {TODAY})
{menu}

## FAQ
{faq}

## Pages
- [Home]({DOMAIN}/)
- [Menu]({DOMAIN}/menu.html)
- [FAQs]({DOMAIN}/faq.html)
- [Blog]({DOMAIN}/blog.html)
{{BLOG_LINKS}}
"""
    llms = llms.replace("{BLOG_LINKS}", "\n".join(
        f"  - [{x['title']}]({DOMAIN}/blog-{x['slug']}.html): {x['summary']}" for x in POSTS))
    posts = "\n\n".join(f"### {x['title']}\n{DOMAIN}/blog-{x['slug']}.html\n\n" + "\n\n".join(
        ("#### " + t[3:]) if t.startswith("## ") else t for t in x["body"]) for x in POSTS)
    full = llms.replace("## Pages", f"## Blog posts\n\n{posts}\n\n## Pages")
    return robots, sitemap, llms, full


NOT_FOUND = """<section><div class="wrap" style="text-align:center">
<h1>Page not found</h1><p>That page has moved or doesn't exist.</p>
<a class="btn" href="./">Back to home</a></div></section>"""


def nice_date(d):
    return date.fromisoformat(d).strftime("%-d %B %Y")


def build_faq():
    faq = "".join(f"<details><summary>{escape(q)}</summary><p>{escape(a)}</p></details>" for q, a in FAQ)
    body = f"""<div class="wrap menu-head">
<span class="tag">FAQs</span>
<h1>Frequently asked questions</h1>
<p>Everything you need to know about Eatfit, from our best-sellers to where to order.</p>
</div>
<section class="faq" style="padding-top:8px"><div class="wrap"><div style="max-width:780px">{faq}</div></div></section>"""
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q,
                              "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}
    return page("faq.html", "FAQs | Eatfit",
                "Answers about Eatfit: best-selling dishes, cities, where to order, calories, protein, veg and Jain options.",
                body, [faq_ld])


def build_blog():
    cards = "".join(
        f'<a class="post" href="blog-{x["slug"]}.html"><img src="{x["image"]}" alt="{escape(x["title"])}" loading="lazy">'
        f'<div><time datetime="{x["date"]}">{nice_date(x["date"])}</time>'
        f'<h3>{escape(x["title"])}</h3><p>{escape(x["summary"])}</p><span>Read more &rarr;</span></div></a>'
        for x in POSTS)
    body = f"""<div class="wrap menu-head">
<span class="tag">Blog</span>
<h1>The Eatfit blog</h1>
<p>Simple ideas for eating well, from the Eatfit kitchen.</p>
</div>
<section style="padding-top:24px"><div class="wrap"><div class="posts">{cards}</div></div></section>"""
    blog_ld = {"@context": "https://schema.org", "@type": "Blog", "name": "The Eatfit blog", "url": DOMAIN + "/blog.html",
               "blogPost": [{"@type": "BlogPosting", "headline": x["title"], "datePublished": x["date"],
                             "url": f"{DOMAIN}/blog-{x['slug']}.html"} for x in POSTS]}
    return page("blog.html", "Blog | Eatfit", "Simple ideas for eating well, from the Eatfit kitchen.", body, [blog_ld])


def build_post(x):
    paras = "".join(f"<h2>{escape(t[3:])}</h2>" if t.startswith("## ") else f"<p>{escape(t)}</p>" for t in x["body"])
    others = "".join(f'<li><a href="blog-{o["slug"]}.html">{escape(o["title"])}</a></li>' for o in POSTS if o is not x)
    body = f"""<article class="wrap article">
<a class="back" href="blog.html">&larr; All posts</a>
<time datetime="{x["date"]}">{nice_date(x["date"])} &middot; Team Eatfit</time>
<h1>{escape(x["title"])}</h1>
<img class="cover" src="{x["image"]}" alt="{escape(x["title"])}" width="640" height="360">
{paras}
<div class="note"><b>Hungry?</b> Order Eatfit on <a href="{ORDER["Swiggy"]}" target="_blank" rel="noopener">Swiggy</a>, <a href="{ORDER["Zomato"]}" target="_blank" rel="noopener">Zomato</a> or <a href="{ORDER["Ownly"]}" target="_blank" rel="noopener">Ownly</a>, or <a href="menu.html">see the menu</a>.</div>
<h3 style="margin-top:40px">More from the blog</h3><ul class="more">{others}</ul>
</article>"""
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": x["title"], "description": x["summary"],
          "datePublished": x["date"], "image": f"{DOMAIN}/{x['image']}", "author": {"@type": "Organization", "name": "Eatfit"},
          "publisher": {"@type": "Organization", "name": "Eatfit", "logo": {"@type": "ImageObject", "url": DOMAIN + "/assets/img/logo.png"}},
          "mainEntityOfPage": f"{DOMAIN}/blog-{x['slug']}.html"}
    return page(f"blog-{x['slug']}.html", f"{x['title']} | Eatfit blog", x["summary"], body, [ld])


def write(name, content):
    with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
        f.write(content)


if __name__ == "__main__":
    sections = load_menu()
    write("assets/style.css", CSS.strip() + "\n")
    write("index.html", build_home(sections))
    write("menu.html", build_menu(sections))
    write("faq.html", build_faq())
    write("blog.html", build_blog())
    for x in POSTS:
        write(f"blog-{x['slug']}.html", build_post(x))
    write("404.html", page("404.html", "Not found | Eatfit", TAGLINE, NOT_FOUND, []))
    robots, sitemap, llms, full = build_seo(sections)
    write("robots.txt", robots)
    write("sitemap.xml", sitemap)
    write("llms.txt", llms)
    write("llms-full.txt", full)
    write(".nojekyll", "")
    n = sum(len(items) for _, _, items in sections)
    print(f"Built Home + Menu ({len(sections)} sections, {n} dishes) + SEO files")
