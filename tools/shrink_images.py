"""Re-encode a game's PNG/JPEG images as WebP under their own names.

shrink_images.py <folder> [quality]

Ren'Py's image loader recognises the format by its contents, so a file keeps
its name and the game's code its references. A file is only replaced when
the WebP is smaller.
"""
import os, sys
from concurrent.futures import ProcessPoolExecutor
from PIL import Image

QUALITY = int(sys.argv[2]) if len(sys.argv) > 2 else 85


def shrink(path):
    before = os.path.getsize(path)
    if before < 32 * 1024:
        return before, before
    try:
        with Image.open(path) as im:
            if getattr(im, "n_frames", 1) > 1:
                return before, before
            im.load()
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA" if "A" in im.getbands() or "transparency" in im.info else "RGB")
            tmp = path + ".webp-tmp"
            im.save(tmp, "WEBP", quality=QUALITY, method=4)
    except Exception as e:
        print("skip", path, e)
        return before, before
    after = os.path.getsize(tmp)
    if after < before:
        os.replace(tmp, path)
        return before, after
    os.remove(tmp)
    return before, before


if __name__ == "__main__":
    files = [os.path.join(d, n) for d, _, ns in os.walk(sys.argv[1]) for n in ns
             if n.lower().endswith((".png", ".jpg", ".jpeg"))]
    with ProcessPoolExecutor() as ex:
        sizes = list(ex.map(shrink, files, chunksize=16))
    b = sum(s[0] for s in sizes); a = sum(s[1] for s in sizes)
    print(f"{len(files)} images: {b / 2**20:.0f} MB -> {a / 2**20:.0f} MB")
