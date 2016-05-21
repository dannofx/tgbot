from tgbot.commands.command import Command
import requests
import html

from threading import Thread


class JokeCommand(Command):
    def __init__(self, logger, message_sender):
        """Constructor.

        Args:
            logger: Object used to generate logs
            messag_sender: object used to send messages to an specified chat_id
        """
        super().__init__(logger, message_sender)

    def tell_joke(self, chat_id):
        """ Download and parse a Chuck Norris joke, this method is NOT inherited 
            from command, is just used for this specific command.

        Args:
            chat_id: Chat identifier of conversation where this command was 
                     was invoked, it's necessary to send a response.
        """
        url = 'http://api.icndb.com/jokes/random'
        self.logger.info("Downloading joke...")
        r = requests.get(url)
        joke = html.unescape(r.json()['value']['joke'])
        self.message_sender.send_message(chat_id, joke)

    def name(self):
        """ Command's name.

        Returns:
            The name for this command.
        """       
        return 'chuck'

    def description(self):
        """ Command's description.

        Returns:
            The short description for this command.
        """   
        return 'Tells a random joke about Chuck Norris.'

    def process(self, chat_id, username, arguments):
        """ This method is called when the command is invoked.

        Args:
            chat_id: Chat identifier of conversation where this command was 
                     was invoked.
            username: User name (or nick) of the user that invoked the command, if 
                      the user doesn't have user name it should contain the
                      registered name.
            arguments: Arguments for the command, if any.
        """
        thread = Thread(target=self.tell_joke, args=(chat_id,))
        thread.start()

    def help(self):
        """ Help text for the command.

        Returns:
            A string with the help related to this command.
        """  
        return self.get_file_help(__file__, "chuck.man")
