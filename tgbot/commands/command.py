import csv
import os

chat_id_index = 0
user_id_index = 1
action_index = 2

class Command:
    def __init__(self, logger, message_sender):
        self.logger = logger
        self.message_sender = message_sender
        self.expected_replies = []
        self.expected_replies_limit = 100

    def process(self, chat_id, user_id, username, arguments):
        raise NotImplementedError("Subclasses should implement this!")
    def process_expected_reply(self, chat_id, user_id, username, reply, action_id):
        ''' optional implementation '''
        pass
    def help(self):
        raise NotImplementedError("Subclasses should implement this!")
    def name(self):
        raise NotImplementedError("Subclasses should implement this!")
    def description(self):
        raise NotImplementedError("Subclasses should implement this!")
    def stop(self):
        '''Optional method used to clean data before program finished'''
        pass
    def get_comma_arguments(argument):
            argument = argument.replace('”','"').replace('“','"')
            splitter = csv.reader(argument.split('\n'), delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, skipinitialspace=True)
            items = []
            for item in splitter:
                items.extend(item)
            return items
    get_comma_arguments = staticmethod(get_comma_arguments)

    def get_file_help(self, script_file, file_name):
        data = ""
        __location__ = os.path.realpath( 
                    os.path.join(os.getcwd(), os.path.dirname(script_file)))
        file_path = os.path.join(__location__, file_name)
        with open (file_path, "r") as myfile:
            data=myfile.read()
        if data == "":
            return "No help available"
        else:
            return data

    def is_user_privileged(self, username):
        users = self.message_sender.get_privileges()
        return username in users.privileged_users or self.is_user_admin(username)
    def is_user_admin(self, username):
        users = self.message_sender.get_privileges()
        return username in users.admins or self.is_user_root(username)
    def is_user_root(self, username):
        users = self.message_sender.get_privileges()
        return users.root == username and users.root != ""        

    def register_for_reply(self, chat_id, user_id, action_id=0):
        register = self.get_expected_reply(chat_id, user_id)
        if register is not None:
            register[action_index] = action_id
            return

        register = [chat_id, user_id, action_id]
        self.expected_replies.insert(0,register)

        lenr = self.expected_replies_limit - len(self.expected_replies)
        if lenr < 0:
            del self.expected_replies[lenr:]

    def is_waiting_reply(self, chat_id, user_id):
        return self.get_expected_reply(chat_id, user_id) is not None

    def register_received_reply(self, chat_id, user_id):
        register = self.get_expected_reply(chat_id, user_id)
        
        if register is not None:
            self.expected_replies.remove(register)
            return register[action_index]
        else:
            return 0

    def get_expected_reply(self, chat_id, user_id):
        for reply in self.expected_replies:
            if reply[chat_id_index] == chat_id and \
                reply[user_id_index] == user_id:
                return reply
        return None

class MessageSender:
    def send_message(self, chat_id, message):
        raise NotImplementedError("Subclasses should implement this!")
    def send_location(self, chat_id, latitude, longitude):
        raise NotImplementedError("Subclasses should implement this!")
    def get_privileges(self):
        raise NotImplementedError("Subclasses should implement this!")
    def get_triggers(self):
        raise NotImplementedError("Subclasses should implement this!")
    def update_message_triggers(self):
        raise NotImplementedError("Subclasses should implement this!")
    def get_configuration(self): 
        raise NotImplementedError("Subclasses should implement this!")
