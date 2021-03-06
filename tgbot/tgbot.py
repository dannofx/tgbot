#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from DictObject import DictObject
from chatterbot import ChatBot
from chatterbot.training.trainers import ChatterBotCorpusTrainer
from textblob.exceptions import MissingCorpusError
from tgbot.commands import commands
from tgbot.commands.command import MessageSender
from tgbot.global_constants import *
from tgbot import tglog

import random
import argparse
import configparser
import json
import requests
import time
import os
import re
import textblob.download_corpora

# Telegram http methods
get_updates_method = "getUpdates"
send_message_method = "sendMessage"
send_location_method = "sendLocation"
bot_info_method = "getMe"

# Constants
CONFIG_ENV_VAR = "TGBOT_CONFIG"

# Global variables
bot_profile = None
logger = None
chatbot = None
chat_events = None
message_triggers = None
configuration = None
pending_hide_keyboard = False

# MessageSender to be used by the commands
class TelegramSender(MessageSender):
    def send_message(self, chat_id, message, enable_preview=True, force_hide = False):
        send_message(chat_id, message, enable_preview, force_hide)    
    def send_location(self, chat_id, latitude, longitude):
        send_location(chat_id, latitude, longitude)
    def send_options(self, chat_id, options, text = 'Select an option:'):
        send_options(chat_id, options, text)
    def request_location(self, chat_id, text='Provide location'):
        request_location(chat_id, text)
    def get_privileges(self):
        return load_permissions()
    
    def get_triggers(self):
        global message_triggers
        return message_triggers
    
    def update_message_triggers(self):
       load_message_triggers() 
    def get_configuration(self):
        return configuration

# Util methods
def static_var(varname, value):
    def decorate(func):
        setattr(func, varname, value)
        return func
    return decorate

def create_url(method_name):
        return create_url.url_format.format(token=create_url.bot_token, method_name=method_name)

def parse_command(text):
    if text is None or text == "" or text ==" ":
        return (None, None, None)
    components = text.split(" ")
    command = components[0]
    arguments = text[len(command)+1:]
    if arguments == '':
        arguments = None
    if not command.startswith("/"):
        return (None, None, None)
    command = command[1:]
    components = command.split("@")
    command = components[0]
    user = None
    if len(components)>1:
        user = components[1]
    return (command, user, arguments) 

def direct_message(message):
    mention = "@" + bot_profile.username
    direct_conversation = is_direct_conversation(message)
    first_component = message.text.split(' ')[0]
    first_component = first_component.split(':')[0]
    starts_mention = first_component == mention
    is_direct_message = direct_conversation or starts_mention
    clean_message = None
    if is_direct_message:
        clean_message = message.text[len(mention):] if message.text.startswith(mention) else message.text
        clean_message = clean_message[1:] if clean_message.startswith(':') else clean_message
        clean_message = clean_message[1:] if clean_message.startswith(' ') else clean_message
    else:
        clean_message = message.text
    return (is_direct_message, clean_message)

def is_direct_conversation(message):
    return (message['from'].id == message.chat.id)

def customize_reply(message, reply):
    if is_direct_conversation(message):
        return reply
    else:
        name = None
        if hasattr(message['from'], 'username'):
            name = '@'+message['from'].username
        else:
            name = message['from'].first_name
        return '{name}: {reply}'.format(name=name, reply=reply)

def choice_reply_randomlyf( choices, receiver_name):
    reply = choice_reply_randomly(choices)
    if reply is None:
        return None
    else:
        return reply.format(name=receiver_name)

def choice_reply_randomly( choices):
    if len(choices) == 0:
        return None
    else:
        reply =  random.choice(choices)
        return reply

def config_file_path():
    if CONFIG_ENV_VAR in os.environ:
        file_path = os.environ[CONFIG_ENV_VAR]
    else:
        current_directory = os.path.dirname(os.path.realpath(__file__))
        file_path = os.path.join(current_directory, "config", "tgbot.cfg")
    return file_path;

def load_message_triggers():
    global message_triggers
    global configuration
    logger.info("Loading message triggers...")
    triggers_file = configuration.get('Message triggers', 'file_path')
    if os.path.isfile(triggers_file):
        with open(triggers_file) as data_file:    
            message_triggers = json.load(data_file)
            message_triggers = DictObject.objectify(message_triggers)
    else:
        logger.info("Creating triggers file: " + triggers_file)
        message_triggers = []
        json.dump(message_triggers, open(triggers_file, 'w'))

def load_permissions():
    permissions = None
    permissions_file = configuration.get('Privileges', 'permissions_file')
    logger.info("Loading permissions...")
    if os.path.isfile(permissions_file):
        with open(permissions_file) as data_file:
            permissions = json.load(data_file)
            permissions = DictObject.objectify(permissions)
    else:
        logger.info("Creating permissions file: " + permissions_file)
        permissions = {
                        "root": "",
                        "admins": [],
                        "privileged_users": []
                      }
        json.dump(permissions, open(permissions_file, 'w'))
    
    return permissions



#Initialization
def main():
    global logger
    global scheduler
    global chatbot
    global chat_events
    global message_triggers
    global configuration
    parser = argparse.ArgumentParser(description="Telegram bot program")
    parser.add_argument("-l", "--log", help="File to write log", default=None, metavar="FILE")
    parser.add_argument("-a", "--authorization-token",  metavar="AUTHORIZATION_TOKEN", 
                        help="Set new Telegram authorization token", default=None) 
    parser.add_argument("-v", "--verbose", help="Enable verbose mode", action='store_true', default=None) 
    parser.add_argument("-t", "--train", help="Train chat bot based on the english corpus", action='store_true', default=None) 
    parser.add_argument("-c", "--config-file",  metavar="CONFIG_FILE", 
                        help="Set configuration file", type=argparse.FileType('r'))
    args = parser.parse_args()

    #Logger configuration
    logging_level = None
    if args.verbose:
        logging_level = logging.INFO
    logger = tglog.config_logger(name = LOGGER_NAME, log_file = args.log, replace_stdout=True, logLevel=logging_level)

    #Configuration file
    config_file = args.config_file
    config = configparser.RawConfigParser()
    if not config_file is None:
        config.readfp(config_file)
    else:
        config_path = config_file_path()
        logger.info("Loading configuration file: {file}".format(file=config_path))
        if config_path is None or not os.path.isfile(config_path):
            logger.error("Config file:{config_file} doesn't exist.".format(config_file=config_path)) 
            logger.error("Please provide a configuration file via -c argument or setting up {var_name} environment variable.".format(var_name=CONFIG_ENV_VAR))
            return 1
        config.read(config_path)
    configuration = config
    logger.info("Configuration file loaded sucessfully")
    
     # Set new token if necessary
    if args.authorization_token:
        config.set('Telegram', 'bot_token', args.authorization_token)
        with open(config_path, 'w') as configfile:
            config.write(configfile)
        logger.info('New authorization token saved.')

    # Get Telegram API properties
    create_url.url_format = config.get('Telegram','url_format')
    create_url.bot_token = config.get('Telegram', 'bot_token')
    if create_url.bot_token == 'TOKEN_BOT':
        logger.error("bot_token is missing, please add a token to tgbot.cgf")
        logger.error("Full config path: " + config_file_path())
        return 1
    
    # Load chat events
    events_file = config.get('Chat events', 'file_path')
    with open(events_file) as data_file:    
        chat_events = json.load(data_file)
        chat_events = DictObject.objectify(chat_events)
    logger.info("Loading chat events...")
    
    # Load message events
    load_message_triggers()
    # Load permissions
    load_permissions()
    # Chat bot configuration
    chatbot_db = config.get('Chatterbot', 'db_path')
    try:
        chatbot = init_chatbot(chatbot_db)
    except MissingCorpusError:
        logger.warning("Corpora needs to be downloaded in order to use Chatterbot... downloading")
        textblob.download_corpora.download_all()
        chatbot = init_chatbot(chatbot_db)

    if args.train:
        logger.info("Bot is being trained...")
        chatbot.set_trainer(ChatterBotCorpusTrainer)
        chatbot.train("chatterbot.corpus.english")
    logger.info("Chatterbot initialized...")
    logger.info("Bot token: " + create_url.bot_token)
   
    # Load message commands
    sender = TelegramSender()
    commands.load_commands(sender, logger)

    # Telegram listener
    try:
        logger.info("Retrieving bot profile...")
        get_bot_profile() 
        logger.info("Listening for incoming messages...")
        while True:
            get_updates()
    except GeneratorExit:
        clean_program()
    except KeyboardInterrupt:
        clean_program()
    else:
        clean_program()
    
    #Finish
    logger.info("Telegram bot terminated")

def clean_program():
    commands.stop_commands()

def init_chatbot(chatbot_db):
    return ChatBot("Terminal",
                storage_adapter = "chatterbot.adapters.storage.JsonDatabaseAdapter",
                logic_adapters = ["chatterbot.adapters.logic.MathematicalEvaluation",
                                 "chatterbot.adapters.logic.TimeLogicAdapter",
                                 "chatterbot.adapters.logic.ClosestMatchAdapter"],
                io_adapters = ["chatterbot.adapters.io.TerminalAdapter"],
                database=chatbot_db, logging=True)

# Telegram profile, receiver and sender functions
@static_var("last_id", None)
@static_var("start", None)
def get_updates():
    get_updates.last_id
    get_updates.start

    if get_updates.start is None:
        get_updates.start = time.time()
    
    url = create_url(get_updates_method)

    params = {'timeout':3600}
    if not get_updates.last_id is None:
        params["offset"] = get_updates.last_id
        params["limit"] = 100
    try:
        response = requests.post(url, params=params)
    except ConnectionError as ce:
        logger.error("Connection Error: " + str(ce))
        return
    except Exception as e:
        logger.error("Unexpected error: " +str(e))
        return
    try:
        data = response.json()
    except ValueError:
        logger.error("Received data could not be parsed")
        return
    if data["ok"]:
        results = data["result"]
        for result in results:
            if "message" in result:
                message = result["message"]
            elif "edited_message" in result:
                continue
            else:
                continue            
            get_updates.last_id = result["update_id"]+1
            if message["date"] >= get_updates.start:
                process_received_message(message)

def get_bot_profile():
    global bot_profile
    url = create_url(bot_info_method)
    response = requests.get(url)
    if response.status_code>= 400:
        logger.error('url: %s', url)
        logger.error('response: %s - %s', response.status_code, response.text)
    data = response.json()
    if data["ok"]:
        bot_profile = DictObject.objectify(data["result"])

def send_message(chat_id, text, enable_preview = True, force_hide = False):
    global pending_hide_keyboard
    url = create_url(send_message_method)   
    params = {'chat_id':chat_id, 'text':text}
    params['disable_web_page_preview'] = not enable_preview
    if pending_hide_keyboard or force_hide:
        params['reply_markup'] = {'hide_keyboard':True}
        pending_hide_keyboard = False
    response = requests.post(url, data=json.dumps(params), headers={'Content-Type': 'application/json'})
    logger.info("Telegram response: "+ str(response.json()))

def send_location(chat_id, latitude, longitude):
    global pending_hide_keyboard
    url = create_url(send_location_method)
    params = {'chat_id':chat_id, 'latitude':latitude, 'longitude':longitude}
    if pending_hide_keyboard:
        params['reply_markup'] = {'hide_keyboard':True}
        pending_hide_keyboard = False
    response = requests.post(url, data=json.dumps(params), headers={'Content-Type': 'application/json'})
    logger.info("Telegram response: "+ str(response.json()))

def send_options(chat_id, options, text = 'Select and option'):

    if len(options) == 0:
        logger.error('Empty array found in options!')
        return
    options_json = []
    for list_x in options:
        if len(list_x) == 0:
            logger.error('Empty array found in options!')
            return
        list_json_x = []
        for element in list_x:
            opt_json = {
                            'text': element
                       }
            list_json_x.append(opt_json)
        options_json.append(list_json_x)

    url = create_url(send_message_method)
    reply_markup = {
                        'keyboard':options_json,
                        'one_time_keyboard': True
                    }
    data = {
                'chat_id':chat_id, 
                'text': text,
                'reply_markup': reply_markup
            }
    response = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
    logger.info("Telegram response: "+ str(response.json()))

def request_location(chat_id, text='Provide location'):
    url = create_url(send_message_method)
    reply_markup = {
                        'keyboard':[[{'text':'Get location','request_location': True}]],
                        'one_time_keyboard': True
                    }
    data = {
                'chat_id':chat_id, 
                'text': text,
                'reply_markup': reply_markup
            }
    response = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json'})
    logger.info("Telegram response: "+ str(response.json()))

def process_received_message(message):
    global pending_hide_keyboard
    logger.info(message)
    message = DictObject.objectify(message)
    username = message['from'].username if hasattr(message['from'], 'username') else None

    processed_event = process_chat_event(message)#text or location
    if not processed_event:
        is_text = hasattr(message, 'text')
        if not is_text:
            #if it's not text it will not be processed for commands or direct message
            process_no_text_message(message, username)
            return

        processed_command = process_command(message, username)
        if not processed_command:
            processed_reply = commands.process_expected_reply(message.chat.id,\
                                                                message['from']['id'],\
                                                                username,\
                                                                message.text)
            if processed_reply:
                # Processed as reply, won't continue
                pending_hide_keyboard = True
                return 
            (direct_msg, clean_text) = direct_message(message)
            direct_conversation = is_direct_conversation(message)
            if direct_msg:
                process_chat_message(message, clean_text)
            if not direct_msg or direct_conversation:
                process_message_trigger(message, clean_text, username)

def process_chat_event(message):
    reply = None

    if hasattr(message, 'new_chat_participant'):
        if message.new_chat_participant.id == bot_profile.id:
            reply = choice_reply_randomlyf(chat_events.new_conversation_add, message.new_chat_participant.first_name)
        else:
            reply = choice_reply_randomlyf(chat_events.new_chat_participant, message.new_chat_participant.first_name)
    elif hasattr(message, 'left_chat_participant'):
        if message.left_chat_participant.id != bot_profile.id:
            reply = choice_reply_randomlyf(chat_events.left_chat_participant, message.left_chat_participant.first_name)
    elif hasattr(message, 'new_chat_title'):
        if message['from'].id != bot_profile.id:
            reply = choice_reply_randomlyf(chat_events.new_chat_title, message['from'].first_name)
    elif hasattr(message, 'new_chat_photo'):
        if message['from'].id != bot_profile.id:
            reply = choice_reply_randomlyf(chat_events.new_chat_photo, message['from'].first_name) 
    elif hasattr(message, 'delete_chat_photo'):
        if message['from'].id != bot_profile.id:
            reply = choice_reply_randomlyf(chat_events.delete_chat_photo, message['from'].first_name)
    elif hasattr(message, 'group_chat_created'):
        if message['from'].id != bot_profile.id:
            reply = choice_reply_randomlyf(chat_events.group_chat_created, message['from'].first_name)
    
    if reply:
        send_message(message.chat.id, reply)
        return True
    else:
        return False

def process_no_text_message(message, username):
    global pending_hide_keyboard
    if hasattr(message, 'text'):
        return False
    processed = False
    if hasattr(message, 'location'):
        processed = commands.process_expected_reply(message.chat.id,\
                                        message['from']['id'],\
                                        username,\
                                        message.location)
        if processed:
            pending_hide_keyboard = True
        
    return processed

def process_command (message, username):
    (command, bot, argument) = parse_command(message.text)
    if (command == None):
        return False
    if (bot is not None) and bot != bot_profile.username:
        return True #it's a command but not for this bot
    #Buscar en lista de comandos y llamar con argumentos
    arguments = []
    try:
        if not argument is None:
            reg = re.compile('(?:["“”].*?["“”]|[^ "“”])+')
            arguments = reg.findall(argument)
    except ValueError:
        #Mostrar tutorial
        send_message(message.chat.id, commands.command_help(command))
        return True
    feedback = commands.process_command(command, message.chat.id, message['from']['id'] ,username, arguments)
    if not feedback is None:
        send_message(message.chat.id, feedback)

    return True


def process_chat_message(message, message_text):

    try:
        reply = chatbot.get_response(message_text).text
        reply = customize_reply(message, reply) 
        send_message(message.chat.id,reply)
    except Exception as e:
        logger.error(str(e))
        send_message(message.chat.id,'I can\'t chat right now :(')


def process_message_trigger(message, message_text, username):
    message_text = message_text.lower()
    for trigger in message_triggers:
        if (len(trigger.responses) == 0):
            continue
        valid_user = len(trigger.users) == 0 or (username in trigger.users)
        if not valid_user:
            continue
        for trigger_key in trigger.trigger_keys:
            if trigger_key.lower() in message_text:
                reply = choice_reply_randomly(trigger.responses)
                reply = customize_reply(message, reply)
                send_message(message.chat.id, reply)
                return
