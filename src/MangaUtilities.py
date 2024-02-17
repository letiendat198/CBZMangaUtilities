import os
import shutil
import zipfile
import xxhash

from PIL import Image
from imageio.v2 import imread


class MangaUtilities:
    def __init__(self):
        self.target_dir = None
        self.target_files = None
        self.hash_dict = {}
        self.file_dict = {}

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

    def check_grayscale(self, file, mode):
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

    def calc_xxhash(self, file):
        f = open(file, "rb")
        xhash = xxhash.xxh3_128_hexdigest(f.read())
        return xhash

    def get_group(self, is_grayscale, is_unique):
        calc = is_grayscale << 1 | is_unique
        if calc == 0:
            return "RC"
        elif calc == 1:
            return "UC"
        elif calc == 2:
            return "RBW"
        elif calc == 3:
            return "UBW"
        return "WTF happened"

    def grayscale_and_hash(self, file, mode, progress_callback=None):
        xhash = self.calc_xxhash(file)
        file_name = os.path.basename(file)
        is_unique = None
        is_grayscale = None
        if self.hash_dict.get(xhash, None) is None:  # Hash is unique
            self.hash_dict[xhash] = [file_name]
            is_unique = True
            _, is_grayscale = self.check_grayscale(file, mode)  # Only check grayscale for unique file
        else:  # Hash not unique (Repeating)
            if len(self.hash_dict[xhash]) == 1:  # If there is 1 item, set that item to not unique and update group
                need_modify = self.hash_dict[xhash][0]
                need_modify_obj = self.file_dict[need_modify]
                need_modify_obj["is_unique"] = False
                need_modify_obj["group"] = self.get_group(need_modify_obj["is_grayscale"], need_modify_obj["is_unique"])
            self.hash_dict[xhash].append(file_name)  # Add item to hash key
            is_unique = False
            prev_file_name = self.hash_dict[xhash][0]
            is_grayscale = self.file_dict[prev_file_name]["is_grayscale"]  # Reuse grayscale value of identical file

        self.file_dict[file_name] = {
            "path": file,
            "hash": xhash,
            "is_grayscale": is_grayscale,
            "is_unique": is_unique,
            "group": self.get_group(is_grayscale, is_unique)
        }
        return file, xhash, is_grayscale, is_unique

    def compress_jpeg(self, file, quality, progress_callback=None):
        print("Compressing", file, "at quality", quality)
        image = Image.open(os.path.normpath(file))
        image.save(file, "JPEG", optimize=True, quality=quality)

    def repack(self, file_iterable, out, progress_callback=None):
            with zipfile.ZipFile(out, "w") as zip_obj:
                for file in file_iterable:
                    zip_obj.write(file, arcname=os.path.basename(file))
                    progress_callback.emit(0)
            print("Repacking as", out)
            # shutil.rmtree(path + "\\" + dirname)
