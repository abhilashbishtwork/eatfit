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
        if os.path.basename(src) == "share-logo.jpg":
            continue
        dst = src[:-4] + ".webp"
        if stale(src, dst):
            Image.open(src).save(dst, "WEBP", quality=78, method=6)

    # Share image: Eatfit logo on brand navy (same pattern as Behrouz / EatClub cards).
    # Navy parts of the logo turn white; the pink glasses stay pink.
    src = os.path.join(IMG, "brand-eatfit.png")
    share = os.path.join(IMG, "share-logo.jpg")
    if stale(src, share) or stale(os.path.abspath(__file__), share):
        navy = (31, 42, 92)
        logo = Image.open(src).convert("RGBA")
        px = logo.load()
        for y in range(logo.height):
            for x in range(logo.width):
                r, g, b_, a = px[x, y]
                pinkness = max(0, r - b_) / 255  # glasses are red-heavy, the line art is blue-heavy
                light = (r + g + b_) / 765
                if pinkness > 0.25:
                    px[x, y] = (r, g, b_, a)
                else:
                    # dark ink -> white, white paper -> transparent
                    px[x, y] = (255, 255, 255, min(255, round(a * (1 - light) * 1.7)))
        w = 620
        logo = logo.resize((w, round(logo.height * w / logo.width)), Image.LANCZOS)
        card = Image.new("RGB", (1200, 630), navy)
        card.paste(logo, ((1200 - logo.width) // 2, (630 - logo.height) // 2), logo)
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
