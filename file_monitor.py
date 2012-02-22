import os, time, re, logging
from event import Event

class FileMonitor(object):

    def __init__(self, root):
        self.delay   = 1
        self.dirs    = {}
        self.files   = {}
        self.root    = root 
        self.file_changed  = Event()
        self.dir_changed   = Event()
        self.ignored_dirs  = re.compile("\.git", re.I)
        self.ignored_files = re.compile("\.swp$", re.I)
        self.track(root)


    def track(self, source):
        self.add_dir(source)
        for root, dirs, files in os.walk(source):
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                self.add_dir(dir_path)
            for file in files:
                file_path = os.path.join(root, file)
                self.add_file(file_path)
        logging.info("Tracking directories: %s" % ", ".join(self.dirs))
        logging.info("Tracking files: %s" % ", ".join(self.files))


    def should_ignore(self, path):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            logging.warn("ignored, path %s doesn't exist" % path)
            return True
        elif re.search(self.ignored_dirs, path):
            logging.debug("ignored, path %s matches dir pattern" % path)
            return True
        elif os.path.isdir(path):
            logging.debug("okay, path %s doesn't match dir pattern and is a directory" % path)
            return False
        elif re.search(self.ignored_files, path):
            logging.debug("ignored, path %s matches file pattern" % path)
            return True
        else:
            return False 


    def add_dir(self, dir, trigger_event = False):
        dir = os.path.abspath(dir)
        if not os.path.isdir(dir):
            return
        if self.should_ignore(dir):
            return
        self.dirs[dir] = os.stat(dir).st_mtime
        if trigger_event:
            self.dir_changed(dir, 'added')


    def add_file(self, path, trigger_event = False):
        path = os.path.abspath(path)
        if self.should_ignore(path):
            return
        self.files[path] = os.stat(path).st_mtime
        if trigger_event:
            self.file_changed(path, 'added')


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
            entry = os.path.abspath(os.path.join(path, entry))
            if not os.path.isdir(entry) and not entry in self.files.keys():
                self.add_file(entry, trigger_event = True)
            elif os.path.isdir(entry) and not entry in self.dirs.keys():
                self.add_dir(entry, trigger_event = True)
