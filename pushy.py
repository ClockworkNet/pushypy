#! /usr/bin/python
import logging, os, sys, notify_handler

from pusher         import * 
from file_monitor   import FileMonitor
from optparse       import OptionParser


class Main(object):
    def __init__(self):
        options, args = self.parse_args()
        log_format    = "%(asctime)s - %(message)s"
        date_format   = "%b %d, %H:%M:%S"

        logging.basicConfig(format=log_format, datefmt=date_format, level=options.log_level)

        # Add notifications
        notify_handler.register(logging.getLogger(), "Pushy")
        
        dir = os.path.abspath(options.source) if options.source else './'

        self.monitor = FileMonitor(dir)

        if options.ignored_dirs:
            self.ignored_dirs = re.compile(options.ignored_dirs, re.I)
        if options.ignored_files:
            self.ignored_files = re.compile(options.ignored_files, re.I)

        self.monitor.delay         = options.delay if options.delay else 1
        self.monitor.file_changed += self.handle_change
        self.monitor.dir_changed  += self.handle_change

        if options.target:
            target = os.path.abspath(options.target)
            if options.username and options.hostname:
                self.pusher = SshPusher(dir, target, options.hostname, options.username)
            else:
                self.pusher = Pusher(dir, target)
        else:
            print "You might want to specify a target directory. This script isn't very useful otherwise."
            self.pusher = None

        logging.info("Pushy started.")
        try:
            self.monitor.start()
        except (KeyboardInterrupt, SystemExit):
            logging.info("Pushy stopped.")
            sys.exit()
        except:
            raise


    def parse_args(self):
        parser = OptionParser(description="Pushes filesystem changes to a target directory")
        parser.add_option("-t", "--target",
            help="The target directory.",
            type="string"
        )
        parser.add_option("-s", "--source", 
            help="The source directory. Default is current directory.",
            type="string",
            default="./"
        )
        parser.add_option("-u", "--username", 
            help="A username. If supplied, files will be pushed via ssh.",
            type="string"
        )
        parser.add_option("-r", "--remote-host",
            dest="hostname",
            help="The name of the host that will receive files. Used for ssh pushes.",
            type="string"
        )
        parser.add_option("-l", "--log-level",
            dest="log_level",
            help="The logger level to use.",
            type="int",
            default=logging.INFO
        )
        parser.add_option("-d", "--delay",
            help="The number of seconds to pause between filesystem scans.",
            type="int",
            default=1
        )
        parser.add_option("--ignored-files",
            dest="ignored_files",
            help="If a file matches this regex, it is ignored.",
            type="string"
        )
        parser.add_option("--ignored-dirs",
            dest="ignored_dirs",
            help="If a directory matches this regex, it is ignored.",
            type="string"
        )

        return parser.parse_args()


    def handle_change(self, path, action):
        logging.debug("Handling change event '%s' for path '%s'" % (action, path))
        if self.pusher is None:
            return
        if action == "deleted":
            self.pusher.remove(path)
        elif action == "added":
            self.pusher.add(path)
        elif action == "updated":
            self.pusher.update(path)

if __name__ == "__main__":
    Main()
