from tgbot.commands.command import Command
import json
import shlex
import collections

KEYS_NOT_FOUND = 0
SOME_KEYS_FOUND = 1
KEYS_FOUND = 2

class TriggerCommand(Command):

    privileges = None
    triggers_file = None
    triggers = None

    def __init__(self, logger, message_sender):
        super().__init__(logger, message_sender)

    def process(self, chat_id, user_id, username, arguments):
        self.privileges = self.message_sender.get_privileges()
        self.configuration = self.message_sender.get_configuration()
        self.triggers_file = self.configuration.get('Message triggers', 'file_path')
        has_privileges = False
        if self.privileges['root'] == username:
            has_privileges = True
        else:
            for admin_username in self.privileges['admins']:
                if admin_username == username:
                    has_privileges = True
                    break

        self.triggers = self.message_sender.get_triggers()
        if len(arguments) < 1:
            return self.help()
        operation = arguments[0] 
        command_arguments = arguments[1:]

        #Operations that don't need privileges
        if operation == "list":
            return self.list_triggers(command_arguments)
 
        if not has_privileges:
            return "Sorry, you don't have permission to edit triggers."
 
        #Operations that need privileges
        if operation == "add":
            return self.add_trigger(command_arguments)
        elif operation == "remove":
            return self.remove_trigger(command_arguments)
        elif operation == "mix":
            return self.join_triggers(command_arguments)
        elif operation == "add_user":
            return self.add_user(command_arguments)
        elif operation == "remove_user":
            return self.remove_user(command_arguments)
        elif operation == "add_response":
            return self.add_response(command_arguments)
        elif operation == "remove_response":
            return self.remove_response(command_arguments)
        else:
            return self.help()

    def add_trigger(self, arguments):
        if len(arguments) == 0:
            return self.help()
        new_keys = self.get_comma_arguments(arguments[0])
        for trigger in self.triggers:
            for keyword in trigger["trigger_keys"]:
                for new_key in new_keys:
                    if keyword == new_key:
                        return "One or more keys were already added."
        
        responses = []
        if len(arguments) > 1:
            responses = self.get_comma_arguments(arguments[1])
       
        users = []
        if len(arguments) > 2:
            users = self.get_comma_arguments(arguments[2])
        
        trigger = {
                    "trigger_keys" : new_keys,
                    "users" : users,
                    "responses" : responses
                  }
        self.triggers.append(trigger)
        self.save_triggers()
        return "Trigger added successfully!"

    def remove_trigger(self, arguments):
        if len(arguments) == 0:
            return self.help()
        status = KEYS_NOT_FOUND
        keywords_to_remove  = self.get_comma_arguments(arguments[0])
        triggers_to_remove = []

        for trigger in self.triggers:
            triggerkeys_to_remove = []
            for keyword in trigger["trigger_keys"]:
                for key_to_remove in keywords_to_remove:
                    if key_to_remove == keyword:
                        triggerkeys_to_remove.append(keyword)
                        status = KEYS_FOUND
                        break
            remaining_keys = [x for x in trigger["trigger_keys"] if x not in triggerkeys_to_remove]
            if len(remaining_keys) > 0:
                trigger["trigger_keys"] = remaining_keys
            else:
                triggers_to_remove.append(trigger)

        remaining_triggers = [x for x in self.triggers if x not in triggers_to_remove]
        self.triggers = remaining_triggers
        self.save_triggers()

        if status == KEYS_NOT_FOUND:
            return "I couldn't find triggers that match with the keys you introduced."
        else:
            return "One or more triggers were removed."
    
    def join_triggers(self, trigger_keys):
        if len(trigger_keys) < 2:
            return self.help()
        triggers_to_join = []
        all_trigger_keys = []
        for key in trigger_keys:
            comma_keys = self.get_comma_arguments(key)
            all_trigger_keys.extend(comma_keys)
        trigger_keys = all_trigger_keys

        for trigger in self.triggers:
            if len(trigger_keys) == 0:
                break
            for keyword in trigger["trigger_keys"]:
                found_key = None
                for key_to_join in trigger_keys:
                    if key_to_join == keyword:
                        triggers_to_join.append(trigger)
                        found_key = key_to_join
                        break
                if not found_key is None:
                    trigger_keys.remove(key_to_join)
                    break
        
        if len(triggers_to_join) < 2:
            return "No enough found triggers to mix."

        new_trigger_keys = []
        new_users = []
        new_responses = []
        for trigger in triggers_to_join:
            new_trigger_keys.extend(trigger["trigger_keys"])
            new_users.extend(trigger["users"])
            new_responses.extend(trigger["responses"])

        new_users = list(set(new_users))
        new_trigger = {
                        "trigger_keys" : new_trigger_keys,
                        "users" : new_users,
                        "responses" : new_responses
                      }
        final_triggers = [x for x in self.triggers if x not in triggers_to_join]
        final_triggers.append(new_trigger)
        self.triggers = final_triggers
        self.save_triggers()

        return "Two or more triggers were mixed"

    def add_user(self, arguments):
        if len(arguments) < 2:
            return self.help()
        keywords = self.get_comma_arguments(arguments[0])
        users = self.get_comma_arguments(arguments[1])

        triggers = self.triggers_for_keys(keywords)
        if len(triggers) == 0:
            return "Triggers not found."
        for trigger in triggers:
            trigger["users"].extend(users)
            trigger["users"] = list(set(trigger["users"]))
        self.save_triggers()
        return "The users were added to the indicated triggers"

    def remove_user(self, arguments):
        if len(arguments) < 1:
            return self.help()
        users = None
        if len(arguments) > 1:
            users = self.get_comma_arguments(arguments[1])
        keywords = self.get_comma_arguments(arguments[0])
        triggers = self.triggers_for_keys(keywords)

        if len(triggers) == 0:
            return "No triggers found"
       
        for trigger in triggers:
            if users is None:
                trigger["users"] = []
            else:
                final_users = trigger["users"]
                for user in users:
                    final_users.remove(user)
                trigger["users"] = final_users
        self.save_triggers()
        return "The users were removed"

    def add_response(self, arguments):
        if len(arguments) < 2:
            return self.help()
        keywords = self.get_comma_arguments(arguments[0])
        responses = self.get_comma_arguments(arguments[1])

        triggers = self.triggers_for_keys(keywords)

        if len(triggers) == 0:
            return "No triggers found"

        for trigger in triggers:
            trigger["responses"].extend(responses)
        self.save_triggers()
        return "The responses were added to the indicated triggers"

    def remove_response(self, arguments):
        if len(arguments) < 1:
            return self.help()
        keywords = self.get_comma_arguments(arguments[0])
        responses = None
        if (len(arguments) > 1):
            responses = self.get_comma_arguments(arguments[1])
        triggers = self.triggers_for_keys(keywords)
        
        if len(triggers) == 0:
            return "No triggers found"

        for trigger in triggers:
            if responses is None:
                trigger["responses"] = []
            else:
                 final_responses = trigger["responses"]
                 for response in responses:
                     final_responses.remove(response)
                 trigger["responses"] = final_responses
 
        self.save_triggers()
        return "The responses were removed from the indicated triggers"

    def list_triggers(self, arguments):
        keywords = []
        if len(arguments) > 0:
            keywords = self.get_comma_arguments(arguments[0])
        triggers = self.triggers_for_keys(keywords)
        
        if len(triggers) == 0:
            if len(keywords) == 0:
                return "There aren't configured triggers."
            else:
                return "There aren't configured triggers for the indicated keywords."

        message = "Triggers:"
        for trigger in triggers:
            trigger_desc = "---\n-Trigger keywords:"
            trigger_keywords = "\n".join(trigger["trigger_keys"])
            trigger_responses = "\n".join(trigger["responses"])
            if trigger_responses == "":
                trigger_responses = "No available responses"
            trigger_users = "\n".join(trigger["users"])
            if trigger_users == "":
                trigger_users = "Any user"

            trigger_desc = "\n".join([trigger_desc, trigger_keywords, "-Responses:", trigger_responses, "-Users:", trigger_users])
            message = "\n".join([message, trigger_desc])
        return message

    def triggers_for_keys(self, keys):
       
        if len(keys) == 0:
            return self.triggers
        
        found_triggers = []
        look_keys = keys[:]

        for trigger in self.triggers:
            if len(look_keys) == 0:
                break
            for key in trigger["trigger_keys"]:
                found_key = False
                for current_key in look_keys:
                    if current_key == key:
                        found_triggers.append(trigger)
                        look_keys.remove(current_key)            
                        found_key = True
                        break
                if found_key:
                    break    
        
        return found_triggers
 
    def save_triggers(self):
        with open (self.triggers_file, 'w') as file:
            json.dump(self.triggers, file)
        self.message_sender.update_message_triggers()

    def help(self):
        self.logger.info("Printing help")
        return self.get_file_help(__file__, "trigger.man")

    def name(self):
        return "trigger"
    
    def description(self):
        return "Manages trigger words in the bot"    

