#!/usr/bin/env python

from setuptools import setup
import configparser
from shutil import copyfile
import os
import sys

token_arg = '--token'
token_value = None
systemv_arg = '--with-systemv'
systemv_install = False
systemv_dir = 'etc/init.d'

if token_arg in sys.argv:
    index = sys.argv.index(token_arg)
    sys.argv.pop(index)
    token_value = sys.argv.pop(index)

if systemv_arg in sys.argv:
    index = sys.argv.index(systemv_arg)
    sys.argv.pop(index)
    if os.path.exists(systemv_dir):
        systemv_install = True
    else:
        print ('Your system doesn\'t support System V init scripts.')
        exit(0)

s = setup(name='tgbot',
          version='0.1',
          description='Python Telegram bot',
          author='Danno Heredia',
          author_email='danno@mistercyb.org',
          url='https://github.com/dannofx/tgbot',
          packages=['tgbot', 
                    'tgbot.commands.native_commands',
                    'tgbot.commands.plugin_commands',
                    'tgbot.data', 
                    'tgbot.config'],
          package_dir={'tgbot': '.'},
          package_data={'tgbot.config': ['tgbot.cfg'],
                        'tgbot.data': ['programmedjobs.sqlite','chatterbot.db'],
                        'tgbot.commands.native_commands': ['*.man'],
                        'tgbot.commands.plugin_commands': ['*.man']},
          install_requires=['DictObject'],
          zip_safe=False
          )
lib_path = s.command_obj['install'].install_lib
egg_name = s.command_obj['bdist_egg'].egg_output
egg_name = egg_name.replace('dist/', '')
egg_name = egg_name.replace('dist\\', '')
dist_name = s.command_obj['install'].config_vars['dist_name']
installation_path = os.path.join(lib_path, egg_name, dist_name)

config_file = os.path.join(installation_path, 'config', 'tgbot.cfg')
config = configparser.RawConfigParser()
config.read(config_file)
db_path = 'sqlite:///' + installation_path +'/data/programmedjobs.sqlite'
config.set('Message Scheduler','db_path', db_path)
db_path = os.path.join(installation_path, 'data', 'chatterbot.db')
config.set('Chatterbot', 'db_path', db_path)
if not token_value is None:
    config.set('Telegram', 'bot_token', token_value)
file_path = os.path.join(installation_path, 'data', 'chat_events.json')
config.set('Chat events', 'file_path', file_path)
file_path = os.path.join(installation_path, 'data', 'message_triggers.json')
config.set('Message triggers', 'file_path', file_path)
file_path = os.path.join (installation_path, 'data', 'permissions.json')
config.set('Privileges', 'permissions_file', file_path)

with open(config_file, 'w') as configfile:
        config.write(configfile)
print ('Configuration file was set up: ' + config_file)

if systemv_install:
    src = 'tgbot'
    destiny = os.path.join(systemv_dir,'tgbot')
    copyfile(src, destiny)

    fdes = open(destiny,'r')
    filedata = fdes.read()
    fdes.close()

    data = filedata.replace('TGBOT_DIR', installation_path)

    fdes = open(destiny,'w')
    fdes.write(data)
    fdes.close()
    
    print ("System V init script was installed.")
