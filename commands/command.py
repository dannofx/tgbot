import csv

class Command:
    def __init__(self, logger, message_sender):
        self.logger = logger
        self.message_sender = message_sender
    def process(self, chat_id, username, arguments):
        raise NotImplementedError("Subclasses should implement this!")
    def help(self):
        raise NotImplementedError("Subclasses should implement this!")
    def name(self):
        raise NotImplementedError("Subclasses should implement this!")
    def description(self):
        raise NotImplementedError("Subclasses should implement this!")
    def get_comma_arguments(argument):
            splitter = csv.reader(argument.split('\n'), delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, skipinitialspace=True)
            items = []
            for item in splitter:
                items.extend(item)
            return items
    get_comma_arguments = staticmethod(get_comma_arguments)

class MessageSender:
    def send_message(self, chat_id, message):
        raise NotImplementedError("Subclasses should implement this!")
    def get_privileges(self):
        raise NotImplementedError("Subclasses should implement this!")
    def get_triggers(self):
        raise NotImplementedError("Subclasses should implement this!")
    def update_message_triggers(self):
        raise NotImplementedError("Subclasses should implement this!")
    def get_configuration(self): 
        raise NotImplementedError("Subclasses should implement this!")
