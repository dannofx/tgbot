from commands.command import Command
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil import parser
from datetime import timedelta
from datetime import datetime
import re
import random


class ScheduleCommand(Command):
    schedule_sender = None
    def __init__(self, logger, message_sender):
        super().__init__(logger, message_sender)
        # Message scheduler configuration
        self.scheduler = BackgroundScheduler()
        configuration = self.message_sender.get_configuration()
        sdb_url = configuration.get('Message Scheduler', 'db_path')
        self.scheduler.add_jobstore('sqlalchemy', url=sdb_url)
        self.scheduler.start()
        ScheduleCommand.schedule_sender = message_sender

    def process(self, chat_id, username, arguments):
        if len(arguments) < 1:
            return self.help()
        
        operation = arguments[0] 
        command_arguments = arguments[1:]

        if operation == "add":
            return self.add_message(username, chat_id, command_arguments)
        elif operation == "time":
            return self.get_local_time()
        elif operation == "remove":
            return self.remove_message(username, command_arguments)
        else:
            return self.help()

    def get_local_time(self):
        date_str =  str(datetime.today().strftime('%Y-%m-%d %H:%M:%S'))
        return "My time is {}".format(date_str)

    def add_message(self, username, chat_id, arguments):
        if len(arguments) <2:
            return self.help()
        date = None
        message = None
        if arguments[0] == 'relative':
            if len(arguments)<3:
                return self.help()
            date = self.on_delta_parse(arguments[1])
            message = arguments[2]
        else:
            date = self.on_date_parse(arguments[0])
            message = arguments[1]
        
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]

        reference = self.user_reference(username)
        if date is None:
            return "{}Date format not recognized".format(reference)

        current_date = datetime.today()
        if date < current_date:
            current_str = self.get_human_string_date(current_date)
            return "{}Sorry, I can't travel to the past, my current date is: {}".format(reference, current_str)
 
        message_id = str(random.randrange(0, 999999999))
        self.scheduler.add_job(ScheduleCommand.send_programmed_message, \
                'date', run_date=date, args=[username, \
                chat_id, message], id = message_id) 
        
        date_str = self.get_human_string_date(date)
        return "{}The message [{}] has been successfully scheduled on {}"\
                .format(reference,  message_id, date_str)

    def send_programmed_message(username, chat_id, message):
        reference = ScheduleCommand.user_reference(username)
        text = "{}{}".format(reference, message)
        ScheduleCommand.schedule_sender.send_message(chat_id, text)    
    send_programmed_message = staticmethod(send_programmed_message)

    def remove_message(self, username, arguments): 
        if len(arguments) < 1:
            return self.help()
        
        founds = 0
        ids = self.get_comma_arguments(arguments[0])
        
        for message_id in ids:
            job = self.scheduler.get_job(message_id)
            if job == None:
                continue
            if job.args[0] != username:
                continue
            self.scheduler.remove_job(message_id)
            founds += 1
        
        reference = self.user_reference(username)
        if founds == len(ids):
            if len(ids) ==1:
                return "{}The scheduled message was canceled.".format(reference)
            else:
                return "{}The scheduled messages were canceled.".format(reference)
        elif founds > 0:
            return "{}Some scheduled messages were canceled, but some others were not found or you aren't the owner.".format(reference)
        else:
            if len(ids) == 1:
                return "{}The scheduled message was not found or you aren't the owner.".format(reference)
            else:
                return "{}The scheduled message were not found or you aren't the owner.".format(reference)

    def get_human_string_date(self,datetime):
        return str(datetime.strftime('%Y-%m-%d %H:%M:%S'))

    def on_delta_parse(self, text_date):
        regex = re.compile(r'^((?P<days>\d+?)d)?((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?$')
        parts = regex.match(text_date)
        if not parts:
            return None
        parts = parts.groupdict()
        time_params = {}
        valid_params = 0
        for (name, param) in parts.items():
            if param:
                time_params[name] = int(param)
                valid_params = valid_params + 1
        if valid_params == 0:
            return None
        return datetime.now() + timedelta(**time_params)

    def on_date_parse(self, text_date):
        try:
            return parser.parse(text_date, dayfirst = True, yearfirst = True)
        except ValueError:
            return None

    def user_reference(username):
        if username is None:
            return ""
        else:
            return "@{}: ".format(username)
    user_reference = staticmethod(user_reference)

    def help(self):
        return "This is the help for the command"

    def name(self):
        return "schedule_message"
    
    def description(self):
        return "Schedule a message to be sent in a specified date."     
