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

    # Share image: the hero photo, scaled to cover 1200x630.
    hero = os.path.join(IMG, "bowls.jpg")
    share = os.path.join(IMG, "share.jpg")
    if stale(hero, share):
        im = Image.open(hero).convert("RGB")
        scale = max(1200 / im.width, 630 / im.height)
        im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
        left, top = (im.width - 1200) // 2, (im.height - 630) // 2
        im.crop((left, top, left + 1200, top + 630)).save(share, "JPEG", quality=85)

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
