import importlib
import json

from commands.command import Command
from commands.command import MessageSender
from commands.native_commands import *
from commands.plugin_commands import *

commands = None
logger = None

def load_commands(message_sender, tg_logger = None):
    global logger
    global commands

    logger = tg_logger
    commands = []
    for cls in Command.__subclasses__():
        command = cls(logger, message_sender)
        commands.append(command)

def get_command(command_name):
    for command in commands:
        if command.name() == command_name:
            return command
    return None

def process_command(command_name, chat_id, username, arguments):
    if command_name == 'help':
        return general_help(arguments)

    command = get_command(command_name)
    if command is None:
        return None
    else:
        return command.process(chat_id, username, arguments)

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
    if (not arguments is None) and len(arguments)>0 and arguments[0] == 'l':
        prefix = ""
        message = ""
    else:
        prefix = "/"
        message = "The available commands are: \n\n"
    message = message + prefix +"help - Print the list of available commands (use l as agument to print just the list).\n"
    for command in commands:
        message = message + "{prefix}{name} - {description}\n".format(prefix=prefix, name=command.name(), description=command.description())
    return message
