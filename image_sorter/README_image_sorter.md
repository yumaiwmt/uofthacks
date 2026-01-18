# Image Sorter

Simple interactive script to review images in a folder and move them to `keep` or `discard`.

Usage:

```bash
python image_sorter.py <source_dir> [--keep KEEP_DIR] [--discard DISCARD_DIR] [--no-open]
```

Examples:

```bash
python image_sorter.py "c:/Users/eliss/UofTHacks/testing images"
python image_sorter.py images --keep images/keep --discard images/discard --no-open
```

Notes:
- A CSV log `.image_sort_log.csv` is written inside the source directory to allow resuming.
- On Windows the viewer is opened using the default image viewer. Use `--no-open` to disable automatic opening.
- Supported extensions: `.jpg`, `.jpeg`, `.png` (case-insensitive). You can modify the script to add more.

Controls:
- `y` or `yes`: move image to keep folder
- `n` or `no`: move image to discard folder
- `q`: quit (progress saved)

