import logging
import notify

def register(logger, title):
    handler = NotifyHandler(title)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)


# Used to show logger statements in a notification window
class NotifyHandler(logging.Handler):
    def __init__(self, title=''):
        logging.Handler.__init__(self)
        self.title = title
        notify.init(self.title)

    def emit(self, record):
        notify.send(self.title, record.msg)
