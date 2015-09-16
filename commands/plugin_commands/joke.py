from commands.command import Command
import requests
from bs4 import BeautifulSoup


class JokeCommand(Command):
    def __init__(self, logger, message_sender):
        super().__init__(logger, message_sender)

    def scrape_joke(self):
        html = requests.get("http://www.chistes.com/ChisteAlAzar.asp?n=3")
        soup = BeautifulSoup(html.text, 'html.parser')
        tag = soup.find('div', 'chiste')
        chiste = ''.join(tag.findAll(text=True))
        # xpath: //div[@class="chiste"]/text()
        # chiste = ''.join(node.findAll(text=True)) for node in tag)
        return chiste

    def name(self):
        return 'chiste'

    def description(self):
        return 'Cuenta un chiste aleatorio'

    def process(self, chat_id, username, arguments):
        return self.scrape_joke()

    def help(self):
        return "Uso /chiste"
