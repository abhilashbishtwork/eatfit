"""Derived image assets: WebP copies of every JPEG, the 1200x630 share image
and favicon.ico. Re-run safely; files are only rewritten when the source is newer."""
import glob
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "assets", "img")


def stale(src, dst):
    return not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src)


def main():
    for src in glob.glob(os.path.join(IMG, "*.jpg")):
        if os.path.basename(src) == "share.jpg":
            continue
        dst = src[:-4] + ".webp"
        if stale(src, dst):
            Image.open(src).save(dst, "WEBP", quality=78, method=6)

    # Share image: the Eatfit logo centred on white, 1200x630.
    src = os.path.join(IMG, "brand-eatfit.png")
    share = os.path.join(IMG, "share.jpg")
    if stale(src, share) or stale(os.path.abspath(__file__), share):
        logo = Image.open(src).convert("RGBA")
        bbox = logo.getchannel("A").getbbox() if logo.getchannel("A").getextrema()[0] < 255 else None
        if bbox:
            logo = logo.crop(bbox)
        w = 640
        logo = logo.resize((w, round(logo.height * w / logo.width)), Image.LANCZOS)
        card = Image.new("RGB", (1200, 630), (255, 255, 255))
        card.paste(logo, ((1200 - logo.width) // 2, (630 - logo.height) // 2), logo)
        card.paste((228, 0, 124), (0, 606, 1200, 630))
        card.save(share, "JPEG", quality=92)

    # favicon.ico: the tiger mark from the left of the logo, on white.
    logo = os.path.join(IMG, "logo.png")
    ico = os.path.join(ROOT, "favicon.ico")
    if stale(logo, ico):
        im = Image.open(logo).convert("RGBA")
        mark = im.crop((0, 0, im.height, im.height))
        bg = Image.new("RGBA", mark.size, (255, 255, 255, 255))
        bg.alpha_composite(mark)
        bg.save(ico, sizes=[(16, 16), (32, 32), (48, 48)])


if __name__ == "__main__":
    main()
