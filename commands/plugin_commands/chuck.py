from commands.command import Command
import requests
import html

from threading import Thread


class JokeCommand(Command):
    def __init__(self, logger, message_sender):
        super().__init__(logger, message_sender)

    def tell_joke(self, chat_id):
        url = 'http://api.icndb.com/jokes/random'
        r = requests.get(url)
        joke = html.unescape(r.json()['value']['joke'])
        self.message_sender.send_message(chat_id, joke)

    def name(self):
        return 'chuck_norris'

    def description(self):
        return 'Cuenta un chiste aleatorio sobre Chuck Norris'

    def process(self, chat_id, username, arguments):
        thread = Thread(target=self.tell_joke, args=(chat_id,))
        thread.start()

    def help(self):
        help_list = [
            self.description(),
            "Uso /chuck_norris",
        ]
        return '\n'.join(help_list)
