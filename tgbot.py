# coding=utf-8
from __future__ import unicode_literals
__author__ = 'luckydonald'
from DictObject import DictObject
from pytg.receiver import Receiver # get messages
from pytg.sender import Sender # send messages, and other querys.
from pytg.utils import coroutine
from pytg import Telegram
from chatterbot import ChatBot
from apscheduler.schedulers.background import BackgroundScheduler

import random
import html.parser
import sys
import os
import shlex
import datetime

current_user = {"username":"mastoBOT","first_name":"Ignacio","last_name":"Villaldama BOT"}
current_user = DictObject.objectify(current_user) 

chatbot = ChatBot("Terminal",
    storage_adapter="chatterbot.adapters.storage.JsonDatabaseAdapter",
    logic_adapter="chatterbot.adapters.logic.EngramAdapter",
    io_adapter="chatterbot.adapters.io.TerminalAdapter",
    database="/home/danno/tgbot/chatterbot.db", logging=True)

scheduler = BackgroundScheduler()

sender = None

def main():
    global sender
    tg = Telegram(
                   telegram="/home/danno/tg/bin/telegram-cli",
                   pubkey_file="/home/danno/tg/tg-server.pub")
    receiver = tg.receiver
    sender = tg.sender
    sender.set_username(current_user.username)
    sender.set_profile_name(current_user.first_name, current_user.last_name)
    # get a Receiver instance, to get messages.
    #receiver = Receiver(host="localhost", port=4458)

    # get a Sender instance, to send messages, and other querys.
    #sender = Sender(host="localhost", port=4458)
    # start the Receiver, so we can get messages!
    receiver.start() # note that the Sender has no need for a start function.

    start_message_scheduler()
        
    # add "example_function" function as message listener. You can supply arguments here (like sender).
    receiver.message(example_function(sender))  # now it will call the example_function and yield the new messages.
    # please, no more messages. (we could stop the the cli too, with sender.safe_quit() )
    receiver.stop()

    # continues here, after exiting while loop in example_function()
    print("I am done!")

    # the sender will disconnect after each send, so there is no need to stop it.
    # if you want to shutdown the telegram cli:
    # sender.safe_quit() # this shuts down the telegram cli.
    # sender.quit() # this shuts down the telegram cli, without waiting for downloads to complete.

#Message Scheduler Section
def send_programmed_message(message, peerID, username):
        print ("Ejecutando tarea programada")
        if username != u"":
            reply = u"@{user_name}: {text}".format(user_name=username, text=message)
        else:
            reply = message
        sender.send_msg(peerID, reply)
def simple_message(message, peerID, username):
    print ("Simple message")

def start_message_scheduler():
    url = 'sqlite:////home/danno/tgbot/programmedjobs.sqlite'
    scheduler.add_jobstore('sqlalchemy', url=url)
    #scheduler.add_jobstore('mongodb', collection='tgbot_jobs')
    scheduler.start()

def stop_message_scheduler():
    scheduler.shutdown()

def schedule_message(date, message, peerID, username):
    scheduler.add_job(send_programmed_message, 'date', run_date=date, args=[message, peerID, username])

# this is the function which will process our incoming messages
@coroutine
def example_function(sender): # name "example_function" and given parameters are defined in main()
	try:
		while True: # loop for messages
			msg = (yield) # it waits until the generator has a has message here.
			sender.status_online()  # so we will stay online.
			print(msg)
			if msg.own: # the bot has send this message.
				continue # we don't want to process this message.
			elif "action" in msg:
				on_action_received(sender, msg)
			elif "text" in msg and msg.text is not None:
				direct_message = on_direct_message_received( msg)
				if not direct_message:
					on_text_message_received(sender, msg)
	except GeneratorExit:
		# the generator (pytg) exited (got a KeyboardIterrupt).
		stop_message_scheduler()
	except KeyboardInterrupt:
		# we got a KeyboardIterrupt(Ctrl+C)
		stop_message_scheduler()
	else:
		# the loop exited without exception, becaues _quit was set True
		stop_message_scheduler()

def on_action_received(sender, message):
	if message.action.type == u"chat_del_user":
		print("Delete user")
		sender.send_msg(message.peer.cmd, u"Bueno, lo vamos a extrañar.")
	elif message.action.type == u"chat_add_user" or message.action.type == u"chat_add_user_link":
		print("Add user")
		reply =  u"Hola, {user_name}. Eres bienvenido!".format(user_name=message.action.user.first_name)
		sender.send_msg(message.peer.cmd, reply)

def on_direct_message_received(message):
    nick = u"@{user_name}".format(user_name=current_user.username)
        
    if (message.text.startswith(nick)):
        html_parser = html.parser.HTMLParser()
        clean_message = message.text.replace(nick,'',1)
        if (clean_message.startswith(':')):
            clean_message = clean_message.replace(':','',1)
        print (clean_message)
        command_processed = process_command(sender, message, clean_message)
        if command_processed is True:
            return True
        reply = chatbot.get_response(clean_message)
        reply = html_parser.unescape(reply)
        if message.sender.username != u"":
             reply = u"@{user_name}: {text}".format(user_name=message.sender.username, text=reply)
        sender.send_msg(message.peer.cmd, reply)
        return True
    else:
        print ("False")
        return False	

def on_text_message_received(sender, message):
        special_filters = [{"contains":"http://", "users":["ecandelas","mrdanno","razpeitia", "hacksxor"],"responses":["Ahí vienen con sus links", "Deja lo leo.", "Ya llegó esa hora del día en que compartes sabiduría","Ya lo había visto."]},{"contains":"https://", "users":["ecandelas","mrdanno","razpeitia", "hacksxor"],"responses":["Ahí vienen con sus links", "Deja lo leo.", "Ya llegó esa hora del día en que compartes sabiduría","Ya lo había visto."]},{"contains":"oh, yeah", "users":[],"responses":["HELL YEAH", "Mega genial!! Wuu!!", "WUUUUU! Vamos muchachos!!","OH YEAH, BABY!! HELL YEAH!!"]},{"contains":"hacking", "users":[],"responses":["Hoy tengo hambre de hacking!", "Hacking time!", "Vamos por más hacking!!","Hacking, hell yeah!",]}]
        special_filters = DictObject.objectify(special_filters)
        messagetext = message.text.lower()
        for filter in special_filters:
                if len(filter.responses) == 0:
                    continue
                valid_user = (message.sender.username in filter.users) or len(filter.users) == 0
                print (valid_user)
                print (filter.contains.lower())
                if filter.contains.lower() in messagetext and valid_user:
                        reply = random.choice(filter.responses)
                        reply = u"@{user_name}: {text}".format(user_name=message.sender.username, text=reply)
                        sender.send_msg(message.peer.cmd, reply)
                        return True
        return False

def process_command(sender, message, clean_message):
    try:
        components = shlex.split(clean_message)
    except ValueError:
        return False
    components_length = len(components)
    print ("Revisando por comandos")
    if components_length == 0:
        return False
    print ("Posible comando")
    command = components[0]
    if command == '!sch_message':
        print ("Comando detectado " + command)
        process_schedule_command(sender, message, components)
        return True
    else:
        if command.startswith('!'):
            reply =  "Comando invalido o sintaxis incorrecta"
            sender.send_msg(message.peer.cmd, reply)
            return True
        else:
            return False

def process_schedule_command(sender, message, arguments):
    valid_command = len(arguments) == 3
    if valid_command:
        try:
            print (arguments[1])
            date = datetime.datetime.strptime(arguments[1], '%d/%m/%Y %H:%M:%S') 
            text = arguments[2]
            schedule_message(date, text, message.peer.cmd, message.sender.username)
            reply = "El mensaje ha quedado exitosamente programado en la siguiente fecha: "+str(date)
            if message.sender.username != u"":
                 reply = u"@{user_name}: {text}".format(user_name=message.sender.username, text=reply)
            sender.send_msg(message.peer.cmd, reply)
            return
        except ValueError:
            pass

    reply = ("Este comando programa un mensaje para ser enviado en una fecha determinada.\n\n"
             "La forma apropiada de utilizarlo es: !sch_message \"DIA/MES/AÑO HORA:MINUTO:SEGUNDO\" \"COMENTARIO\"\n\n"
             "Un ejemplo sería: !sch_message \"03/10/2015 23:00:00\" \"Un saludo para todos.\"\n\n"
             "Te comento que los mensajes son programados en mi hora local, la cual es: "+str(datetime.datetime.now()))
    if message.sender.username != u"":
         reply = u"@{user_name}: {text}".format(user_name=message.sender.username, text=reply)
    sender.send_msg(message.peer.cmd, reply)

## program start here ##
if __name__ == '__main__':
	main()	# executing main function.
			# Last command of file (so everything needed is already loaded above)
