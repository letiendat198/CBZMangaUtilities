import os


class FileHelper:
    def __init__(self, file_name):
        self.file_name = file_name

    def write(self, content):
        f = open(self.file_name, 'a', encoding='utf-8')
        f.write(content + '\n')
        f.close()

    def overwrite(self, content):
        f = open(self.file_name, 'w', encoding='utf-8')
        f.write(content + '\n')
        f.close()

    def read(self):
        f = open(self.file_name, 'r', encoding='utf-8')
        return f.read()

    def read_bytes(self):
        f = open(self.file_name, 'rb')
        return f.read()

    def exists(self):
        return os.path.isfile(self.file_name)

    def delete(self):
        os.remove(self.file_name)
