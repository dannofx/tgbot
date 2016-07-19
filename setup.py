#!/usr/bin/env python3

from setuptools import setup
import configparser
from shutil import copyfile
import os
import stat
import sys

version = __import__('tgbot').__version__
author = __import__('tgbot').__author__
author_email = __import__('tgbot').__email__

just_configure = False

token_arg = '--authorization-token'
token_value = None
systemv_arg = '--with-systemv'
systemv_install = False
systemv_dir = '/etc/init.d'
configure_arg = 'just-configure'

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

if configure_arg in sys.argv:
  index = sys.argv.index(configure_arg)
  sys.argv.pop(index)
  just_configure = True
  

def install_module():   
    s = setup(name='tgbot',
              version=version,
              description='Python Telegram bot',
              author=author,
              author_email=author_email,
              url='https://github.com/dannofx/tgbot',
              packages=['tgbot',
                        'tgbot.commands',
                        'tgbot.commands.native_commands',
                        'tgbot.commands.plugin_commands',
                        'tgbot.data', 
                        'tgbot.config'],
              package_dir={'tgbot': 'tgbot'},
              package_data={'tgbot.config': ['tgbot.cfg'],
                            'tgbot.data': ['chat_events.json'],
                            'tgbot.commands.native_commands': ['*.man'],
                            'tgbot.commands.plugin_commands': ['*.man']},
              install_requires=['DictObject', 
                                'chatterbot<=0.4.4',
                                'apscheduler',
                                'python-dateutil',
                                'SQLAlchemy',
                                'bs4'],
              license='BSD',
              zip_safe=False,
              keywords=['telegram', 'bot', 'tgbot']
              )
    lib_path = s.command_obj['install'].install_lib
    egg_name = s.command_obj['bdist_egg'].egg_output
    egg_name = egg_name.replace('dist/', '')
    egg_name = egg_name.replace('dist\\', '')
    dist_name = s.command_obj['install'].config_vars['dist_name']
    installation_path = os.path.join(lib_path, egg_name, dist_name)
    return installation_path

def install_systemv():
    # Launch script
    launch_script = None
    if just_configure:
        container = os.path.dirname(os.path.realpath(__file__))
        launch_script = 'tgbot_run.py'
        launch_script = os.path.join(container,launch_script)
    else:
        launch_script = 'tgbot_run.sh'
        destiny = os.path.join(installation_path,launch_script)
        copyfile(launch_script, destiny)
        launch_script = destiny
    st = os.stat(launch_script)
    os.chmod(launch_script, st.st_mode | stat.S_IEXEC)

    #Service script
    src = 'tgbot.srv'
    destiny = os.path.join(systemv_dir,'tgbot')
    copyfile(src, destiny)

    fdes = open(destiny,'r')
    filedata = fdes.read()
    fdes.close()

    data = filedata.replace('TGBOT_LAUNCH', launch_script)

    fdes = open(destiny,'w')
    fdes.write(data)
    fdes.close()

    st = os.stat(destiny)
    os.chmod(destiny, st.st_mode | stat.S_IEXEC)

    print ("System V init script was installed.")

def setup_configfile(installation_path):
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


installation_path = None
if just_configure:
    installation_path = os.path.dirname(os.path.realpath(__file__))
    installation_path = os.path.join(installation_path, 'tgbot')
    print ('tgbot module won\'t be installed but the current project will be configured to use absolute paths.')
else:
    installation_path = install_module()

setup_configfile(installation_path)

if systemv_install:
    install_systemv()
