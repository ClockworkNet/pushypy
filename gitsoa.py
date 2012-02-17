#! /usr/bin/python
import os, time, sys, re

class FileMonitor(object):

    def __init__(self):
        self.delay   = 1
        self.dirs    = {}
        self.files   = {}
        self.ignored = re.compile("^\.", re.I)


    def add_dir(self, dir):
        dir = os.path.abspath(dir)
        if not os.path.exists(dir) or not os.path.isdir(dir):
            print "Bad dir path: ", dir
            return
        if self.should_ignore(dir):
            print "skipping ", dir 
            return
        self.dirs[dir] = os.stat(dir).st_mtime
        entries = os.listdir(dir)
        for entry in entries:
            entry = os.path.join(dir, entry)
            if os.path.isdir(entry):
                self.add_dir(entry)
            else:
                self.add_file(entry)

    def add_file(self, path):
        if not os.path.exists(path) or not os.path.exists(path):
            print "Bad file path: ", path
            return
        path = os.path.abspath(path)
        self.files[path] = os.stat(path).st_mtime


    def should_ignore(self, path):
        base = os.path.basename(path)
        return re.match(self.ignored, base)


    def start(self):
        while True:
            for path, modified in self.dirs.items():
                self.check_dir(path, modified)
            for path, modified in self.files.items():
                self.check_file(path, modified)
            time.sleep(self.delay)


    def check_file(self, path, last_modified):
        if not os.path.exists(path):
            del self.files[path]
            self.file_changed(path, 'deleted')
            return

        modified = os.stat(path).st_mtime
        if last_modified != modified:
            self.files[path] = modified
            self.file_changed(path, 'updated')


    def check_dir(self, path, last_modified):
        if not os.path.exists(path):
            del self.dirs[path]
            self.dir_changed(path, 'deleted')
            return
        # look for new files
        entries = os.listdir(path)
        for entry in entries:
            entry = os.path.join(path, entry)
            if self.should_ignore(entry):
                continue
            if not os.path.isdir(entry) and not entry in self.files.keys():
                self.add_file(entry)
                self.file_changed(entry, 'added')
            elif os.path.isdir(entry) and not entry in self.dirs.keys():
                self.add_dir(entry)
                self.dir_changed(entry, 'added')


    def file_changed(self, path, action):
        print "File ", path, action


    def dir_changed(self, path, action):
        print "Dir ", path, action


def main(args):
    fm = FileMonitor()
    dir = args[0] if len(args) > 0 else "./"
    fm.add_dir(dir)
    fm.start()

if __name__ == "__main__":
    main(sys.argv[1:])
