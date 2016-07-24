import importlib
import json

from tgbot.commands.command import Command
from tgbot.commands.command import MessageSender
from tgbot.commands.native_commands import *
from tgbot.commands.plugin_commands import *

commands = None
logger = None
message_sender = None

def load_commands(msg_sender, tg_logger = None):
    global logger
    global commands
    global message_sender

    logger = tg_logger
    commands = []
    message_sender = msg_sender
    for cls in Command.__subclasses__():
        command = cls(logger, message_sender)
        commands.append(command)

def stop_commands():
    for command in commands:
        command.stop()

def get_command(command_name):
    for command in commands:
        if command.name() == command_name:
            return command
    return None

def process_command(command_name, chat_id, user_id, username, arguments):
    if command_name == 'help':
        return general_help(arguments)

    command = get_command(command_name)
    if command is None:
        return None
    else:
        return command.process(chat_id, user_id, username, arguments)

def process_expected_reply(chat_id, user_id, username, reply):
    processed = False
    for command in commands:
        if command.is_waiting_reply(chat_id, user_id):
            action_id = command.register_received_reply(chat_id, user_id)
            feedback = command.process_expected_reply(chat_id,user_id, username, reply, action_id)
            if  feedback is not None and isinstance(feedback, str):
                message_sender.send_message(chat_id, feedback, force_hide = True)
            processed = True
    return processed

def command_help(command_name):
    if command_name == 'help':
        return general_help()
 
    command = get_command(command_name)
    if command is None:
        return general_help()
    else:
        return command.help()

def general_help(arguments = None):
    prefix = None
    message = None
    argument = None
    if (not arguments is None) and len(arguments)>0:
        argument = arguments[0]
        if argument != 'l':
            command = get_command(argument)
            if not command is None:
                return command.help()

    if argument == 'l':
        prefix = ""
        message = ""
    else:
        prefix = "/"
        message = "The available commands are: \n\n"
    message = message + prefix +"help - Print the list of available commands (use l as agument to print just the list).\n"
    for command in commands:
        message = message + "{prefix}{name} - {description}\n".format(prefix=prefix, name=command.name(), description=command.description())
    return message
