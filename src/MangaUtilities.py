import os
import shutil
import zipfile

from PIL import Image
from imageio.v2 import imread


class MangaUtilities:
    def __init__(self):
        self.target_dir = None
        self.target_files = None

    def unpack(self, file_path, dest, progress_callback=None):
        self.target_dir = dest + "\\" + os.path.basename(file_path).strip(".zip")
        # os.makedirs(target_dir)
        with zipfile.ZipFile(file_path, 'r') as zip_obj:
            zip_obj.extractall(self.target_dir)
        print("Unpacking " + file_path + " to " + self.target_dir)
        self.target_files = []
        for root, dirs, files in os.walk(self.target_dir):
            for file in files:
                if file.endswith(".jpeg") or file.endswith(".jpg") or file.endswith(".png"):
                    self.target_files.append(os.path.join(root,file))
        return self.target_dir, self.target_files

    def check_grayscale(self, file, mode, progress_callback=None):
        print("Checking grayscale for", file)
        img = imread(file)
        if len(img.shape) < 3:
            return file, True
        w_divisor = 1
        h_divisor = 1
        if mode == "Quarter":
            h_divisor = 2
            w_divisor = 2
        elif mode == "Half-H":
            h_divisor = 1
            w_divisor = 2
        elif mode == "Half-V":
            h_divisor = 2
            w_divisor = 1
        img = Image.open(file)
        img = img.convert("RGB")
        w, h = img.size
        for i in range(int(w / w_divisor)):
            for j in range(int(h / h_divisor)):
                r, g, b = img.getpixel((i, j))
                if r != g != b:
                    # print(file, "is colored")
                    return file, False
            # print(file, "is grayscale")
        return file, True

    def compress_jpeg(self, file, quality, progress_callback=None):
        image = Image.open(file)
        image.save(file, "JPEG", optimize=True, quality=quality)

    def repack(self, path, out, option, progress_callback=None):
        for dirname in os.listdir(path):  # List all directories in path
            member_path = []
            for roots, dirs, files in os.walk(os.path.join(path, dirname)):  # Index all file in sub directories
                for file in files:
                    member_path.append(roots + "\\" + file)
            with zipfile.ZipFile(out, "w") as zip_obj:
                for file in member_path:
                    if option == 1:
                        zip_obj.write(file, arcname=os.path.relpath(file, os.path.join(path, dirname)))
                    else:
                        if file.endswith(".jpeg"):
                            if file.endswith("cover.jpeg"):
                                zip_obj.write(file, arcname="00000.jpeg")
                                continue
                            zip_obj.write(file, arcname=os.path.basename(file))
            print("Repacking", path, "as", out)
            shutil.rmtree(path + "\\" + dirname)
