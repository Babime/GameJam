import sys
import os
from PIL import Image

def main(folder):
    for fname in sorted(os.listdir(folder)):
        path = os.path.join(folder, fname)
        if not os.path.isfile(path):
            continue
        if not fname.lower().endswith(".png"):
            continue
        with Image.open(path) as img:
            w, h = img.size
            print(f"{fname:25s}  {w} x {h}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py /path/folder")
        sys.exit(1)
    main(sys.argv[1])