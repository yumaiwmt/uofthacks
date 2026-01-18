import argparse
import os
import platform
import subprocess
import shutil
import csv
import sys
from pathlib import Path


def open_file(path: str):
    """Open a file with the default viewer (non-blocking where possible)."""
    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        # Fallback: try to run via webbrowser
        try:
            import webbrowser

            webbrowser.open(path)
        except Exception:
            print(f"Could not open {path} automatically. Please open it manually.")


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def unique_target(target: Path):
    if not target.exists():
        return target
    base = target.stem
    suffix = target.suffix
    parent = target.parent
    i = 1
    while True:
        candidate = parent / f"{base}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def move_file(src: Path, dst_dir: Path):
    ensure_dir(dst_dir)
    dst = dst_dir / src.name
    dst = unique_target(dst)
    shutil.move(str(src), str(dst))
    return dst


def load_logged(log_path: Path):
    seen = {}
    if log_path.exists():
        with log_path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    seen[row[0]] = row[1]
    return seen


def append_log(log_path: Path, filename: str, decision: str):
    with log_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([filename, decision])


def gather_images(src_dir: Path, exts=(".jpg", ".jpeg", ".png")):
    files = []
    for p in sorted(src_dir.iterdir()):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    return files


def interactive_sort(source, keep, discard, logfile, open_images=True):
    src_dir = Path(source).expanduser()
    keep_dir = Path(keep).expanduser()
    discard_dir = Path(discard).expanduser()
    log_path = Path(logfile).expanduser()

    ensure_dir(src_dir)
    ensure_dir(keep_dir)
    ensure_dir(discard_dir)

    logged = load_logged(log_path)
    imgs = gather_images(src_dir)
    if not imgs:
        print("No images found in source directory.")
        return

    for img in imgs:
        # If already logged (moved earlier), skip
        if img.name in logged:
            continue

        print(f"\nFile: {img.name}")
        if open_images:
            open_file(str(img))

        while True:
            try:
                resp = input("Keep? (y/n) [q to quit]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\nQuitting.")
                return

            if resp in ("y", "yes"):
                try:
                    dst = move_file(img, keep_dir)
                    append_log(log_path, img.name, "keep")
                    print(f"Moved to {dst}")
                except Exception as e:
                    print(f"Error moving file: {e}")
                break
            elif resp in ("n", "no"):
                try:
                    dst = move_file(img, discard_dir)
                    append_log(log_path, img.name, "discard")
                    print(f"Moved to {dst}")
                except Exception as e:
                    print(f"Error moving file: {e}")
                break
            elif resp == "q":
                print("Quitting. Progress saved to log.")
                return
            else:
                print("Please answer 'y' or 'n', or 'q' to quit.")

    print("All images processed.")


def sort_image(image_path: str, decision: str, keep_dir: str, discard_dir: str, log_path: str):
    """Sort a single image based on decision ('yes' for keep, 'no' for discard)."""
    img = Path(image_path)
    if decision == 'yes':
        dst = move_file(img, Path(keep_dir))
        append_log(Path(log_path), img.name, "keep")
        print(f"Kept: {dst}")
    elif decision == 'no':
        dst = move_file(img, Path(discard_dir))
        append_log(Path(log_path), img.name, "discard")
        print(f"Discarded: {dst}")
    else:
        raise ValueError("Decision must be 'yes' or 'no'")


def main():
    # Hardcode the source directory here (change this path as needed)
    source = "C:/Users/eliss/UofTHacks/uofthacks/SecondSkin frontend/src/testing images"  # Example path
    # Keep the rest of the options if you want them
    parser = argparse.ArgumentParser(description="Interactive image sorter: move images to keep or discard folders.")
    parser.add_argument("--keep", default="keep", help="Directory to move kept images into (default: keep)")
    parser.add_argument("--discard", default="discard", help="Directory to move discarded images into (default: discard)")
    parser.add_argument("--log", default=None, help="CSV log file path. Default: .image_sort_log.csv inside source dir")
    parser.add_argument("--no-open", action="store_true", help="Don't open images automatically")

    args = parser.parse_args()
    
    # Validation remains the same
    if not os.path.isdir(source):
        print(f"Source directory '{source}' not found.")
        sys.exit(1)

    default_log = os.path.join(source, ".image_sort_log.csv")
    logfile = args.log if args.log else default_log

    interactive_sort(source, args.keep, args.discard, logfile, open_images=not args.no_open)

if __name__ == "__main__":
    main()

