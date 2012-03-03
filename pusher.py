import os, logging, shutil, pwd, subprocess


class Pusher(object):

    def __init__(self, source, target):
        self.source = os.path.abspath(source)
        self.target = os.path.abspath(target)


    def add(self, item):
        name        = os.path.basename(item)
        source_path = os.path.abspath(item)
        target_path = self.determine_destination(item)
        if os.path.exists(target_path):
            logging.error("Skipping add for '%s': file already exists" % name)
        elif os.path.exists(source_path):
            logging.info("Pushing %s to %s" % (name, self.target))
            self.push(source_path, target_path)
        else:
            logging.error("Path %s doesn't exist" % source_path)


    def update(self, item):
        name        = os.path.basename(item)
        source_path = os.path.abspath(item)
        target_path = self.determine_destination(item)

        if not os.path.exists(target_path):
            logging.debug("%s does not exist in target. Adding instead of updating." % name)
            self.add(item)
            return

        source_mod  = os.stat(source_path).st_mtime
        target_mod  = os.stat(target_path).st_mtime

        if target_mod > source_mod:
            logging.warn("Skipping update of %s on target. Target file is more recent that source file." % name)
            return

        logging.info("Updating %s on %s" % (name, self.target))
        self.push(source_path, target_path)


    def remove(self, item):
        name        = os.path.basename(item)
        target_path = self.determine_destination(item)
        
        if not os.path.exists(target_path):
            logging.info("Skipping remove. Target file %s doesn't exist." % name)
            return

        logging.info("Removing %s" % name)
        try:
            if os.path.isdir(target_path):
                os.rmdir(target_path)
            else:
                os.remove(target_path)
        except Exception as err:
            logging.error("Error occurred while removing %s: %s" % (target_path, str(err)))


    def push(self, source_path, target_path):
        try:
            target_dir = os.path.dirname(target_path)
            if not os.path.exists(target_dir):
                logging.info("Creating target directory %s before copying file." % target_dir)
                os.mkdir(target_dir)
            shutil.copy2(source_path, target_path)
        except Exception as err:
            logging.error("Error ocurred while copying file: %s" % str(err))


    def determine_destination(self, item):
        abs_path      = os.path.abspath(item)
        relative_path = os.path.relpath(abs_path, self.source)
        destination   = os.path.join(self.target, relative_path)
        return destination


class SshPusher(Pusher):

    def __init__(self, source, target, hostname="", username=None):
        super(SshPusher, self).__init__(source, target)
        self.hostname = hostname
        if username is None:
            username = pwd.getpwuid(os.getuid())[0]
        self.username = username

    def push(self, source_path, target_path):
        p = subprocess.call(['scp', source_path, "%s@%s:%s" % (self.username, self.hostname, target_path)])

    def remove(self, item):
        target_path = self.determine_destination(item)
        if os.path.isdir(target_path):
            cmd = 'rm -rf'
        else:
            cmd = 'rm'
        p = subprocess.call(['ssh', self.hostname, cmd, target_path])
