from commands.command import Command
import datetime
import requests


class FXCommand(Command):
    FX = {}

    def __init__(self, logger, message_sender):
        super().__init__(logger, message_sender)
        self.configuration = self.message_sender.get_configuration()
        self.ACCESS_KEY = self.configuration.get('FX', 'access_key')

    def get_exchage_rate(self, amount, src_curr, dst_curr):
        FX = self.FX
        src_curr = src_curr.upper().strip()
        dst_curr = dst_curr.upper().strip()

        try:
            amount = float(amount)
        except:
            return "Monto no es un numero"

        should_update = False
        if FX:
            last_update = datetime.datetime.fromtimestamp(FX['timestamp'])
            dt = datetime.datetime.now() - last_update
            if dt >= datetime.timedelta(days=1):
                should_update = True
        else:
            should_update = True

        if should_update:
            url = "http://www.apilayer.net/api/live"
            payload = {
                "access_key": self.ACCESS_KEY,
            }
            r = requests.get(url, params=payload)
            self.logger.info(r.url)
            self.logger.info("Status code: %d", r.status_code)
            self.logger.info(r.text)
            FX.update(r.json())

        src_rate = "USD{0}".format(src_curr)
        dst_rate = "USD{0}".format(dst_curr)
        quotes = FX['quotes']
        if (src_rate not in quotes) or (dst_rate not in quotes):
            return "Exchange Rate {0} {1} not supported".format(src_curr, dst_curr)
        src_rate = quotes[src_rate]
        dst_rate = quotes[dst_rate]
        new_amount = (amount / src_rate) * dst_rate
        return "%.02f %s = %.02f %s" % (amount, src_curr, new_amount, dst_curr)

    def name(self):
        return 'FX'

    def description(self):
        return 'Convierte montos entre diferentes divisas'

    def process(self, chat_id, username, arguments):
        if len(arguments) != 3:
            return self.help()
        else:
            try:
                return self.get_exchage_rate(*arguments)
            except Exception as e:
                self.logger.warning(str(e))
                return "Algo salio mal, checa el log"

    def help(self):
        return "Uso /FX Monto DivisaBase DivisaDestino"
