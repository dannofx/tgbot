from commands.command import Command
import json
import collections

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

    def add_admin(self, username):
        if username is None:
            return self.help()
        for admin in self.privileges['admins']:
            if admin == username:
                return "@{username} is already an admin user.".format(username=username)
        #self.privileges['admins'].append(username)
        self.privileges.setdefault('admins', []).append(username)
        self.save_privileges()
        self.logger.info("AAAAAAA "+str(self.privileges))
        return "@{username} has been added successfully!".format(username=username)

    def remove_admin(self, username):
        if username is None:
            return self.help()
        for admin in self.privileges['admins']:
            if admin == username:
                self.privileges['admins'].remove(admin)
                self.save_privileges()
                return "@{username} has been removed successfully.".format(username=username)
        return "@{username} is not in the admins list".format(username=username)


    def add_privileged_user(self, username):
        if username is None:
            return self.help()
        for puser in self.privileges['privileged_users']:
            if puser == username:
                return "@{username} is already an privileged user.".format(username=username)
        self.privileges['privileged_users'].append(username)
        #self.privileges.setdefault('privileged_users', []).append(username)
        self.save_privileges()
        return "@{username} has been added successfully!".format(username=username)

    def remove_privileged_user(self, username):
        if username is None:
            return self.help()
        for privileged_user in self.privileges['privileged_users']:
            if privileged_user == username:
                self.privileges['privileged_users'].remove(privileged_user)
                self.save_privileges()
                return "@{username} has been removed successfully.".format(username=username)
        return "@{username} is not in the privileged_users list".format(username=username)
   
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
        return "This is the help for the command"

    def name(self):
        return "admin"
    
    def description(self):
        return "Manage user privilieges"     
