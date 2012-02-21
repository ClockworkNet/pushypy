#! /usr/bin/python
import os, time, sys, re, logging, shutil

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
            logging.info("ignored, path %s matches dir pattern" % path)
            return True
        elif os.path.isdir(path):
            logging.info("okay, path %s doesn't match dir pattern and is a directory" % path)
            return False
        elif re.search(self.ignored_files, path):
            logging.info("ignored, path %s matches file pattern" % path)
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
            entry = os.path.join(path, entry)
            if not os.path.isdir(entry) and not entry in self.files.keys():
                self.add_file(entry, trigger_event = True)
            elif os.path.isdir(entry) and not entry in self.dirs.keys():
                self.add_dir(entry, trigger_event = True)


class Event(object):
    def __init__(self):
        self.handlers = set()

    def handle(self, handler):
        self.handlers.add(handler)
        return self

    def unhandle(self, handler):
        try:
            self.handlers.remove(handler)
        except:
            raise ValueError("Handler is not handling this event, so cannot unhandle it.")
        return self

    def fire(self, *args, **kargs):
        for handler in self.handlers:
            handler(*args, **kargs)

    def getHandlerCount(self):
        return len(self.handlers)

    __add__  = handle
    __sub__  = unhandle
    __call__ = fire
    __len__  = getHandlerCount


class Pusher(object):

    def __init__(self, source, target):
        self.source = os.path.abspath(source)
        self.target = os.path.abspath(target)


    def add(self, item):
        source_path = os.path.abspath(item)
        target_path = self.determine_destination(item)
        if os.path.exists(target_path):
            logging.error("Skipping add for '%s': file already exists" % item)
        elif os.path.exists(source_path):
            logging.info("Pushing %s to %s" % (source_path, target_path))
            self.push(source_path, target_path)
        else:
            logging.error("Path %s doesn't exist for adding" % source_path)


    def update(self, item):

        source_path = os.path.abspath(item)
        target_path = self.determine_destination(item)

        if not os.path.exists(target_path):
            logging.info("%s does not exist in target. Adding instead of updating." % item)
            self.add(item)
            return

        source_mod  = os.stat(source_path).st_mtime
        target_mod  = os.stat(target_path).st_mtime

        if target_mod > source_mod:
            logging.warn("Skipping update of %s on target. Target file is more recent that source file." % item)
            return

        logging.info("Updating %s to %s" % (source_path, target_path))
        self.push(source_path, target_path)


    def remove(self, item):
        target_path = self.determine_destination(item)
        
        if not os.path.exists(target_path):
            logging.info("Skipping remove. Target file %s doesn't exist." % target_path)
            return

        logging.info("Removing %s from %s" % (source_path, target_path))
        
        try:
            if os.path.isdir(target_path):
                os.rmdir(target_path)
            else:
                os.remove(target_path)
        except Error, err:
            logging.error("Error occurred while removing %s: %s" % (item, str(err)))


    def push(self, source_path, target_path):
        try:
            shutil.copy(source_path, target_path)
        except Error, err:
            logging.error("Error ocurred while copying file: %s" % str(err))


    def determine_destination(self, item):
        abs_path      = os.path.abspath(item)
        relative_path = os.path.relpath(abs_path, self.source)
        destination   = os.path.join(self.target, relative_path)
        return destination


class Main(object):
    def __init__(self, args):
        dir = os.path.abspath(args[0])

        self.monitor = FileMonitor(dir)
        self.monitor.file_changed += self.handle_change
        self.monitor.dir_changed  += self.handle_change

        if len(args) > 1:
            target = os.path.abspath(args[1])
            self.pusher = Pusher(dir, target)

        self.monitor.start()

    def handle_change(self, path, action):
        print "file changed", path, action
        if action == "deleted":
            self.pusher.remove(path)
        elif action == "added":
            self.pusher.add(path)
        elif action == "updated":
            self.pusher.update(path)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    Main(sys.argv[1:])
