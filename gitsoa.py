#! /usr/bin/python
import os, time, sys, re, logging, subprocess

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
        logging.info("Tracking directories", self.dirs)
        logging.info("Tracking files", self.files)


    def should_ignore(self, path):
        path = os.path.abspath(path)
        if not os.path.exists(path):
            logging.warn("ignored, path doesn't exist", path)
            return True
        elif re.search(self.ignored_dirs, path):
            logging.info("ignored, matches dir pattern", path)
            return True
        elif os.path.isdir(path):
            logging.info("okay, doesn't match dir pattern and is a directory", path)
            return False
        elif re.search(self.ignored_files, path):
            logging.info("ignored, matches file pattern", path)
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


class GitPush(object):

    def __init__(self, source, target):
        self.source = source
        self.target = target


    def add(self, item):
        path = os.path.abspath(item)
        if os.path.exists(path):
            self.call("git add %s" % path)
        else:
            logging.error("File doesn't exist for adding", path)


    def remove(self, item):
        path = os.path.abspath(item)
        self.call("git rm %s" % path)


    def commit(self, msg):
        self.call('git commit -a -m "%s"' % msg.replace('"', '\\"'))


    def export(self):
        if not self.commit("Saving for export to %s" % self.target):
            return
        # @TODO: implement this
        destination = os.path.join(self.target, "backup.zip")
        self.call("git archive --format=zip --output=%s" % destination)


    def call(self, cmd):
        print "calling '%s'" % cmd
        try:
            r = subprocess.call(cmd, shell=True)
            return True
        except:
            logging.error("Error calling command '%s'" % cmd)
            return False


class Main(object):
    def __init__(self, args):
        dir    = os.path.abspath(args[0])

        self.monitor = FileMonitor(dir)
        self.monitor.file_changed += self.handle_change
        self.monitor.dir_changed  += self.handle_change

        if len(args) > 1:
            target = os.path.abspath(args[1])
            self.pusher = GitPush(dir, target)

        self.monitor.start()

    def handle_change(self, path, action):
        print "file changed", path, action
        if action == "deleted":
            self.pusher.remove(path)
        else:
            self.pusher.add(path)
        self.pusher.export()

if __name__ == "__main__":
    Main(sys.argv[1:])
