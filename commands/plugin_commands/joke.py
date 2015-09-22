from commands.command import Command
import requests
from bs4 import BeautifulSoup
from threading import Thread


class JokeCommand(Command):
    def __init__(self, logger, message_sender):
        super().__init__(logger, message_sender)

    def scrape_joke(self, level):
        url = "http://www.chistes.com/ChisteAlAzar.asp?n={0}".format(level)
        self.logger.info(url)
        html = requests.get(url)
        soup = BeautifulSoup(html.text, 'html.parser')
        tag = soup.find('div', 'chiste')
        chiste = ''.join(tag.findAll(text=True))
        return chiste

    def tell_joke(self, chat_id, level):
        joke = self.scrape_joke(level)
        self.message_sender.send_message(chat_id, joke)

    def name(self):
        return 'chiste'

    def description(self):
        return 'Cuenta un chiste aleatorio'

    def process(self, chat_id, username, arguments):
        level = 3
        if len(arguments) == 1:
            try:
                level = int(arguments[0])
            except:
                pass
            if not 1 <= level <= 5:
                level = 3
        thread = Thread(target=self.tell_joke, args=(chat_id, level))
        thread.start()

    def help(self):
        return "Uso /chiste"
