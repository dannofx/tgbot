from tgbot.commands.command import Command
import json
import collections
import os

class AdminCommand(Command):

    privileges = None
    permissions_file = None

    def __init__(self, logger, message_sender):
        super().__init__(logger, message_sender)

    def process(self, chat_id, username, arguments):
        self.privileges = self.message_sender.get_privileges()
        self.configuration = self.message_sender.get_configuration()
        self.permissions_file = self.configuration.get('Privileges', 'permissions_file')
        if self.privileges['root'] =="":
            self.logger.warning("root user not configured in " + permissions_file)
            return "A super user must be manually configured in order to perform admin operations."
        has_privileges = False
        if self.privileges['root'] == username:
            has_privileges = True
        else:
            for admin_username in self.privileges['admins']:
                if admin_username == username:
                    has_privileges = True
                    break

        if not has_privileges:
            return "Sorry, you don't have permission to perform admin operations."
        
        if len(arguments) < 1:
            return self.help()
        operation = arguments[0]
        
        op_user = None
        if len(arguments) > 1:
            op_user = arguments[1]

        if operation == "add_admin":
            return self.add_admin(op_user)
        elif operation == "remove_admin":
            return self.remove_admin(op_user)
        elif operation == "add_privileged_user":
            return self.add_privileged_user(op_user)
        elif operation == "remove_privileged_user":
            return self.remove_privileged_user(op_user)
        elif operation == "list":
            return self.list()
        else:
            return self.help()

    def add_admin(self, usernames_str):
        if usernames_str is None:
            return self.help()
    
        usernames = self.get_comma_arguments(usernames_str)
        message = ""
        for username in usernames:
            can_be_added = True
            for admin in self.privileges['admins']:
                if admin == username:
                    can_be_added = False
                    break

            if can_be_added:
                self.privileges['admins'].append(username)
                message +=  "@{username} has been added successfully!\n".format(username=username)
            else:
                message +=  "@{username} is already an admin user.\n".format(username=username)

        self.save_privileges()
        return message

    def remove_admin(self, usernames_str):
        if usernames_str is None:
            return self.help()

        usernames = self.get_comma_arguments(usernames_str)
        message = ""
        for username in usernames:
            can_be_removed = False
            for admin in self.privileges['admins']:
                if admin == username:
                    can_be_removed = True
                    break
            if can_be_removed:
                self.privileges['admins'].remove(admin)
                message += "@{username} has been removed successfully.\n".format(username=username)
            else:
                message += "@{username} is not in the admins list\n".format(username=username)
        self.save_privileges()
        return message

    def add_privileged_user(self, usernames_str):
        if usernames_str is None:
            return self.help()
    
        usernames = self.get_comma_arguments(usernames_str)
        message = ""
        for username in usernames:
            can_be_added = True
            for admin in self.privileges['privileged_users']:
                if admin == username:
                    can_be_added = False
                    break

            if can_be_added:
                self.privileges['privileged_users'].append(username)
                message +=  "@{username} has been added successfully!\n".format(username=username)
            else:
                message +=  "@{username} is already an privileged user.\n".format(username=username)

        self.save_privileges()
        return message

    def remove_privileged_user(self, usernames_str):
        if usernames_str is None:
            return self.help()

        usernames = self.get_comma_arguments(usernames_str)
        message = ""
        for username in usernames:
            can_be_removed = False
            for admin in self.privileges['privileged_users']:
                if admin == username:
                    can_be_removed = True
                    break
            if can_be_removed:
                self.privileges['privileged_users'].remove(admin)
                message += "@{username} has been removed successfully.\n".format(username=username)
            else:
                message += "@{username} is not in the privileged users list\n".format(username=username)
        self.save_privileges()
        return message

    def list(self):
        message = "-Root user: \n\t@" + self.privileges['root'] + "\n"
        message = "".join((message, "-Admin users:\n"))
        for admin in self.privileges['admins']:
            message = "".join((message, "\t@{admin}\n".format(admin=admin)))
        message = "".join((message, "-Privileged users:\n"))
        for puser in self.privileges['privileged_users']:
            message = "".join((message, "\t@{user}\n".format(user=puser)))
        return message

    def save_privileges(self):
        with open (self.permissions_file, 'w') as file:
            json.dump(self.privileges, file)

    def help(self):
        self.logger.info("Printing help")
        return self.get_file_help(__file__, "admin.man")

    def name(self):
        return "admin"
    
    def description(self):
        return "Manages user privilieges"     
