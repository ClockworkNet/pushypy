import pynotify, logging

class NotifyHandler(logging.Handler):
    def __init__(self, title=''):
        logging.Handler.__init__(self)
        self.title = title
        pynotify.init(self.title)

    def emit(self, record):
        n = pynotify.Notification(self.title, record.msg)
        n.show()
