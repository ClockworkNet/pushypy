#! /usr/bin/python
import os, time

class FileMonitor(object):

    def __init__(self):
        self.delay = 5
        self.dirs = []
        self.files = {}

    def add_dir(self, dir):
        for root, dirs, files in os.walk(dir):
            for child_dir in dirs:
                path = os.path.join(root, child_dir)
                self.dirs.append(path)
            for file in files:
                path = os.path.join(root, file)
                stat = os.stat(path)
                self.files[path] = stat.st_mtime

    def start(self):
        while True:
            time.sleep(self.delay)
            for path in self.dirs:
                self.check_dir(path)
            for path, modified in self.files.items():
                self.check_file(path, modified)

    def check_file(self, path, modified):
        print "Checking file ", path, modified 

    def check_dir(self, path):
        print "Checking dir ", path 

def main(args):
    fm = FileMonitor()
    dir = len(args[0]) ? args[0] : "."
    fm.add_dir(dir)
    fm.start()

if __name__ == "__main__":
    main(sys.argv[1:])
