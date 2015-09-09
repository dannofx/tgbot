from commands.command import Command

class ScheduleCommand(Command):

    def __init__(self, logger, message_sender):
        super().__init__(logger, message_sender)
        self.counter = 0
        self.logger.info("Initializing counter "+ str(self.counter))

    def process(self, chat_id, username, arguments):
        self.logger.info("Scheduling message")
        self.counter = self.counter + 1
        self.logger.info("Incrementing counter "+ str(self.counter))
        return "Message programmed"

    def help(self):
        self.logger.info("Printing help")
        return "This is the help for the command"

    def name(self):
        return "schedule_message"
    
    def description(self):
        return "Schedule a message to be sent in a specified date."     
