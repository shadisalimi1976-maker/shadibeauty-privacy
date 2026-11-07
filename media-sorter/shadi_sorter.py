# -*- coding: utf-8 -*-
r"""
Shadi Media Sorter
------------------
Sorts the photos and videos on a drive into the same categories as the
iPhone shortcut, using a free AI model (CLIP) that runs on this computer.
Nothing is sent to the internet after the one-time model download.

Original files are never deleted. Modes:
  link  (default) each category folder gets a hard link: no extra disk space,
                  the original stays where it is. Needs an NTFS drive.
  move            the original is moved into its category folder. No extra
                  space. Every move is logged and can be undone with --undo.
  copy            a full copy goes into the category folder (uses disk space).

Usage examples:
  python shadi_sorter.py E:\ --limit 100 --dry-run     # test, changes nothing
  python shadi_sorter.py E:\ --limit 100               # first real test
  python shadi_sorter.py E:\                           # whole drive
  python shadi_sorter.py E:\ --undo                    # undo "move" mode
"""

import argparse
import csv
import hashlib
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

OUTPUT_DIR_NAME = "Shadi Organized"
REVIEW = "نیاز به بررسی"

# Category -> English descriptions for CLIP. Order does not matter.
CATEGORIES = {
    "محصولات پوست": [
        "a product photo of a skincare cream jar",
        "a serum bottle with a brand label",
        "skincare products arranged on a table",
        "a cosmetic product package for face care",
    ],
    "محصولات مو": [
        "a product photo of a shampoo bottle",
        "hair care product bottles with labels",
        "a hair oil or hair mask product package",
        "hair conditioner and shampoo products on a shelf",
    ],
    "انیمیشن پوست": [
        "a 3D medical illustration of skin layers",
        "a cartoon animation about skin care",
        "a scientific diagram of a skin cross section",
        "computer graphics animation of skin cells",
    ],
    "انیمیشن مو": [
        "a 3D medical illustration of a hair follicle",
        "a cartoon animation about hair care",
        "a microscopic 3D render of hair strands",
        "computer graphics animation of hair growth",
    ],
    "تصاویر AI پوست": [
        "an extreme close-up photo of facial skin texture",
        "close-up of dry flaky skin on a woman's face",
        "close-up of large pores on cheek skin",
        "before and after comparison of facial skin aging",
    ],
    "کلیپ شادی برای پوست": [
        "a woman talking to the camera while applying cream to her face",
        "a woman showing her skincare routine on her face",
        "a selfie video of a woman applying serum to her face",
        "a woman demonstrating face cleansing in front of the camera",
    ],
    "کلیپ شادی برای مو": [
        "a woman talking to the camera while applying product to her hair",
        "a woman applying serum to her scalp",
        "a selfie video of a woman showing her hair care routine",
        "a woman demonstrating a hair treatment in front of the camera",
    ],
    "خدمات دوبی": [
        "the Dubai skyline with Burj Khalifa",
        "an advertisement for beauty services in Dubai",
        "a luxury beauty salon in Dubai",
    ],
    "کلینیک": [
        "a beauty clinic treatment room",
        "a cosmetic laser device treatment on a patient",
        "a dermatology clinic with medical equipment",
        "an aesthetic clinic procedure on a face",
    ],
    "درمان دست": [
        "close-up of hands receiving skin care treatment",
        "applying cream to the back of the hands",
        "dry rough skin on hands",
    ],
    "سفیدی بدن": [
        "applying whitening lotion on body skin",
        "before and after body skin lightening",
        "body skin brightening treatment on legs or arms",
    ],
    "Personal": [
        "a family photo",
        "friends at a party or a restaurant",
        "a travel photo of a city or nature",
        "a pet dog or cat",
        "a photo inside a living room at home",
        "a group of people posing for a photo",
        "children playing",
    ],
    REVIEW: [
        "a screenshot of a phone screen with text",
        "a document or a page of text",
        "a blurry dark photo",
        "a plain black or empty image",
    ],
}

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".bmp", ".gif", ".tif", ".tiff"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".3gp", ".wmv", ".webm", ".mts"}
SKIP_DIRS = {"$recycle.bin", "system volume information", "windows", "program files",
             "program files (x86)", "programdata", "appdata", "$windows.~bt"}
MIN_SIZE = 15 * 1024          # skip icons and thumbnails
VIDEO_POSITIONS = (0.1, 0.3, 0.5, 0.7, 0.9)


def say(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------- frames ----

def load_image(path):
    from PIL import Image, ImageOps
    img = Image.open(path)
    img.draft("RGB", (448, 448))  # fast JPEG decode at reduced size
    img = ImageOps.exif_transpose(img)
    return img.convert("RGB")


def video_frames(path):
    """Grab frames at 10/30/50/70/90% of the video."""
    import av
    frames = []
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        stream.thread_type = "AUTO"
        duration = None
        if stream.duration and stream.time_base:
            duration = float(stream.duration * stream.time_base)
        elif container.duration:
            duration = container.duration / 1_000_000
        if not duration or duration <= 0:
            for frame in container.decode(stream):
                return [frame.to_image().convert("RGB")]
            return []
        for pos in VIDEO_POSITIONS:
            target = int(duration * pos / stream.time_base) if stream.time_base else 0
            try:
                container.seek(target, stream=stream, any_frame=False, backward=True)
                for frame in container.decode(stream):
                    img = frame.to_image().convert("RGB")
                    img.thumbnail((448, 448))
                    frames.append(img)
                    break
            except Exception:
                continue
    return frames


# ------------------------------------------------------------ classifier ----

class Classifier:
    def __init__(self):
        import torch
        import open_clip
        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        say(f"مدل هوش مصنوعی در حال بارگذاری است ({self.device})... بار اول چند دقیقه طول می‌کشد.")
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            "ViT-B-32", pretrained="laion2b_s34b_b79k", device=self.device)
        self.model.eval()
        tokenizer = open_clip.get_tokenizer("ViT-B-32")
        self.names, prompts = [], []
        for name, texts in CATEGORIES.items():
            for t in texts:
                self.names.append(name)
                prompts.append(t)
        with torch.no_grad():
            tf = self.model.encode_text(tokenizer(prompts).to(self.device))
            self.text = tf / tf.norm(dim=-1, keepdim=True)
        self.categories = list(CATEGORIES)

    def classify(self, images):
        """Returns (category, confidence 0..1)."""
        torch = self.torch
        batch = torch.stack([self.preprocess(im) for im in images]).to(self.device)
        with torch.no_grad():
            f = self.model.encode_image(batch)
            f = f / f.norm(dim=-1, keepdim=True)
            f = f.mean(dim=0, keepdim=True)
            f = f / f.norm(dim=-1, keepdim=True)
            sims = (100.0 * f @ self.text.T)[0]
        best = {}
        for name, s in zip(self.names, sims.tolist()):
            best[name] = max(best.get(name, -1e9), s)
        scores = torch.tensor([best[c] for c in self.categories]).softmax(dim=0)
        i = int(scores.argmax())
        return self.categories[i], float(scores[i])


class FakeClassifier:
    """For testing the program without the AI model (SHADI_FAKE=1)."""
    def classify(self, images):
        w, h = images[0].size
        cats = list(CATEGORIES)
        return cats[(w + h) % len(cats)], 0.9


# ---------------------------------------------------------------- helpers ----

def quick_hash(path, size):
    h = hashlib.sha1(str(size).encode())
    with open(path, "rb") as f:
        h.update(f.read(1 << 20))
        if size > 2 << 20:
            f.seek(-(1 << 20), os.SEEK_END)
            h.update(f.read(1 << 20))
    return h.hexdigest()


def iter_media(root, out_dir):
    out_dir = os.path.normcase(os.path.abspath(out_dir))
    for dirpath, dirnames, filenames in os.walk(root):
        if os.path.normcase(os.path.abspath(dirpath)).startswith(out_dir):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames
                       if d.lower() not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            ext = os.path.splitext(name)[1].lower()
            if ext in IMAGE_EXT or ext in VIDEO_EXT:
                yield os.path.join(dirpath, name), ext in VIDEO_EXT


def unique_target(folder, name):
    target = folder / name
    stem, ext = os.path.splitext(name)
    n = 1
    while target.exists():
        target = folder / f"{stem} ({n}){ext}"
        n += 1
    return target


def open_db(out_dir):
    db = sqlite3.connect(out_dir / "sorter.db")
    db.execute("""CREATE TABLE IF NOT EXISTS files(
        src TEXT PRIMARY KEY, hash TEXT, category TEXT, confidence REAL,
        is_video INTEGER, placed TEXT, status TEXT, ts REAL)""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_hash ON files(hash)")
    db.commit()
    return db


def write_index(db, out_dir):
    path = out_dir / "فهرست فایل‌ها.csv"
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["دسته", "اطمینان", "نوع", "فایل اصلی", "محل در پوشهٔ دسته", "وضعیت"])
        for row in db.execute("SELECT category, confidence, is_video, src, placed, status "
                              "FROM files ORDER BY category, src"):
            cat, conf, vid, src, placed, status = row
            w.writerow([cat, f"{(conf or 0):.0%}", "ویدئو" if vid else "عکس",
                        src, placed or "", status])
    return path


def check_hardlink(out_dir):
    a = out_dir / ".link_test_a"
    b = out_dir / ".link_test_b"
    try:
        a.write_bytes(b"x")
        os.link(a, b)
        return True
    except OSError:
        return False
    finally:
        for p in (a, b):
            try:
                p.unlink()
            except OSError:
                pass


# ------------------------------------------------------------------- undo ----

def undo(out_dir):
    db = open_db(out_dir)
    rows = db.execute("SELECT src, placed FROM files WHERE status='moved'").fetchall()
    say(f"برگرداندن {len(rows)} فایل به جای اصلی...")
    back = 0
    for src, placed in rows:
        if placed and os.path.exists(placed) and not os.path.exists(src):
            os.makedirs(os.path.dirname(src), exist_ok=True)
            shutil.move(placed, src)
            db.execute("UPDATE files SET status='undone', placed=NULL WHERE src=?", (src,))
            back += 1
    db.commit()
    say(f"تمام شد. {back} فایل برگشت.")


# ------------------------------------------------------------------- main ----

def main():
    ap = argparse.ArgumentParser(description="Shadi Media Sorter")
    ap.add_argument("drive", help="drive or folder, e.g. E:\\")
    ap.add_argument("--mode", choices=["link", "move", "copy"], default="link")
    ap.add_argument("--limit", type=int, default=0, help="process only N new files")
    ap.add_argument("--dry-run", action="store_true", help="classify only, change nothing")
    ap.add_argument("--min-confidence", type=float, default=0.30,
                    help="below this, the file goes to " + REVIEW)
    ap.add_argument("--undo", action="store_true", help="undo --mode move")
    args = ap.parse_args()

    root = Path(args.drive)
    if not root.exists():
        say(f"مسیر پیدا نشد: {root}")
        sys.exit(1)
    out_dir = root / OUTPUT_DIR_NAME
    out_dir.mkdir(exist_ok=True)

    if args.undo:
        undo(out_dir)
        return

    if args.mode == "link" and not args.dry_run and not check_hardlink(out_dir):
        say("این هارد از «لینک بدون فضای اضافه» پشتیبانی نمی‌کند (احتمالاً exFAT است).")
        say("یکی از این دو را انتخاب کنید و دوباره اجرا کنید:")
        say("  --mode move   فایل اصلی به پوشهٔ دسته منتقل می‌شود (فضای اضافه نمی‌خواهد، با --undo برمی‌گردد)")
        say("  --mode copy   یک کپی ساخته می‌شود (فضای اضافه می‌خواهد)")
        sys.exit(2)

    clf = FakeClassifier() if os.environ.get("SHADI_FAKE") else Classifier()
    db = open_db(out_dir)
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass

    skip = "('error','dry-run')" if not args.dry_run else "('error')"
    done = {r[0] for r in db.execute(f"SELECT src FROM files WHERE status NOT IN {skip}")}
    placed_states = "('linked','moved','copied')" if not args.dry_run else "('dry-run')"
    counts, processed, start = {}, 0, time.time()
    say(f"شروع: {root}   حالت: {'آزمایشی (بدون تغییر)' if args.dry_run else args.mode}")

    for src, is_video in iter_media(root, out_dir):
        if src in done:
            continue
        if args.limit and processed >= args.limit:
            break
        try:
            size = os.path.getsize(src)
            if size < MIN_SIZE:
                continue
            h = quick_hash(src, size)
            dup = db.execute("SELECT category FROM files WHERE hash=? AND src!=? AND status IN "
                             + placed_states, (h, src)).fetchone()
            if dup:
                db.execute("INSERT OR REPLACE INTO files VALUES(?,?,?,?,?,?,?,?)",
                           (src, h, dup[0], None, int(is_video), None, "duplicate", time.time()))
                processed += 1
                continue

            images = video_frames(src) if is_video else [load_image(src)]
            if not images:
                raise ValueError("no frames")
            category, conf = clf.classify(images)
            if conf < args.min_confidence:
                category = REVIEW

            placed, status = None, "dry-run"
            if not args.dry_run:
                folder = out_dir / category
                folder.mkdir(exist_ok=True)
                target = unique_target(folder, os.path.basename(src))
                if args.mode == "link":
                    os.link(src, target)
                    status = "linked"
                elif args.mode == "move":
                    shutil.move(src, target)
                    status = "moved"
                else:
                    shutil.copy2(src, target)
                    status = "copied"
                placed = str(target)
            db.execute("INSERT OR REPLACE INTO files VALUES(?,?,?,?,?,?,?,?)",
                       (src, h, category, conf, int(is_video), placed, status, time.time()))
            counts[category] = counts.get(category, 0) + 1
        except Exception as e:
            db.execute("INSERT OR REPLACE INTO files VALUES(?,?,?,?,?,?,?,?)",
                       (src, None, REVIEW, None, int(is_video), None, "error", time.time()))
            say(f"  ! خطا روی {src}: {e}")
        processed += 1
        if processed % 25 == 0:
            db.commit()
            rate = processed / max(time.time() - start, 1)
            say(f"  {processed} فایل انجام شد  ({rate:.1f} فایل در ثانیه)")

    db.commit()
    index = write_index(db, out_dir)
    say("")
    say(f"تمام شد. {processed} فایل در این اجرا بررسی شد:")
    for cat, n in sorted(counts.items(), key=lambda x: -x[1]):
        say(f"  {cat}: {n}")
    say(f"فهرست کامل (برای Excel): {index}")


if __name__ == "__main__":
    main()
