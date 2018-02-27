# tgbot #

tgbot is another [Telegram](https://telegram.org/) bot written in Python. It's a multipurpose bot that is able to have a conversation (using [ChatterBot](https://github.com/gunthercox/ChatterBot) library), look for trigger keywords in a conversation and launch automated responses according to them. It also is able to adjust some internal configurations directly from the Telegram app and includes several commands like commands to tell jokes or schedule messages. Custom commands can be added dropping python scripts in the commands folder.

## Installation

tgbot needs Python 3.4 or newer to work and it has been tested on OS X 10.9+ and several Debian based systems. It could work over Windows but it has not been tested yet.

First of all, you need to create a Telegram bot and get a token, if you don't know how to do it, the process is explained [here](https://core.telegram.org/bots#6-botfather).

If you want your bot be able to interact with groups don't forget configure privacy settings for your bot in the [@BotFather](https://telegram.me/BotFather)'s conversation (commands `/setjoingroups` and `/setprivacy`).

Download tgbot:
```
git clone https://github.com/dannofx/tgbot
```
Next, `cd` into tgbot directory and execute the following command:
```
sudo python3 setup.py install --authorization-token YOUR_TOKEN
```
And  start the bot using the following command:
```
sudo python3 -m tgbot
```
At this point, your bot should be running but its commands won't appear in the command menu in Telegram, to add them, first get a list of them sending the following command to your bot in a conversation
```
/help l
```
This will give you a list of commands with their description.

Next, open a conversation with @BotFather and send him the following command:
```
/setcommands
```
Select your bot and paste the command list obtained previously.
### Other installation options

**Running just the local copy**

If you just want to run tgbot but not install it as a module, you can just run the following command:
```
sudo python3 tgbot_run.py --authorization-token YOUR_TOKEN
```
The `authorization-token` flag is just necessary the first time, it will be saved in the configuration file.

**Edit configuration manually**

tgbot can be configured manually editing the file `tgbot/config/tgbot.cfg`, here you can configure the Telegram token or establish absolute paths for other data files. This file initially should have the following content:
```
[Message Scheduler]
db_path = sqlite:///tgbot/data/programmedjobs.sqlite

[Chatterbot]
db_path = tgbot/data/chatterbot.db

[Telegram]
bot_token = TOKEN_BOT
url_format = https://api.telegram.org/bot{token}/{method_name}

[Chat events]
file_path = tgbot/data/chat_events.json

[Message triggers]
file_path = tgbot/data/message_triggers.json

[Privileges]
permissions_file = tgbot/data/permissions.json
```

**Installing just dependencies and configuring local routes**

To just install dependencies and establish absolute paths in the configuration file without install tgbot as a module run the following command:
```
sudo python3 setup.py just-configure --authorization-token YOUR_TOKEN
```

**Install System V init script (Debian based systems)**

If your system supports System V scripts, you can install the boot script passing `with-systemv` parameter to `seup.py` during installation:
```
sudo python3 setup.py install --with-systemv --authorization-token YOUR_TOKEN
```

To complete the installation, enter:
```
sudo update-rc.d tgbot defaults 90 10
```
And now tgbot will run automatically at boot.


## Parameters

tgbot can be executed with the following parameters:
- `-l FILE` or `--log FILE` specifies a file to write log.
- `-a TOKEN` or `--authorization-token TOKEN` specifies and saves a Telegram bot token.
- `-v` or `--verbose` enables verbose mode.
- `-c FILE` or `--config-file FILE` specifies the path to a different configuration file.
- `-t` or `--train` Explained in the next section.

**Train the chat bot**

After installation [ChatterBot](https://github.com/gunthercox/ChatterBot) instance (inside tgbot) starts off without any language knowledge, as it receives input its knowledge will increment, but if you want to accelerate the process, use the parameter `--train` or `-r` as following:
```
sudo python3 -m tgbot --train
```
## Other features


**Group chat events**

The bot can react to different group chat events with automated responses, this responses can be modified in the file `tgbot/data/chat_events.json`. In order your bot can access to these events, the privacy settings must be configurated as previously indicated.

**Triggers**

The bot can detect specific key phrases (triggers) in the conversation and react with costumized responses, these responses can be added, edited and deleted using `/trigger` command (needs permissions) or manually in the file `tgbot/data/message_triggers.json`.

**Permissions**

Some actions like triggers edition need permissions to be performed, you can add admins and privileged users using the command `/admin`, but first you need to set a root user in the file `tgbot/data/permissions.json` (this file is generated after the first run). This is an example of how this should look this file with a root user with user name "daniel_root"

```json
{
  "privileged_users": [],
  "admins": [],
  "root": "daniel_root"
}
```

**Default commands**

This is a list of the default commands in tgbot:

- `/help` - Print the list of available commands (use l as agument to print just the list).
- `/fx` - Currency converter.
- `/trigger` - Manages trigger words in the bot.
- `/chiste` - Gets a joke in Spanish.
- `/schedule_message` - Schedule a message to be sent in a specified date.
- `/admin` - Manages user privileges
- `/chuck` - Tells a random joke about Chuck Norris.

## Custom commands integration

You can create your own commands and add them to your bot instance, to do this create a python file in the directory `tgbot/commands/plugin_commands/`, in this file you will need to create a class inherits from `Command` class. The file `chuck.py` that contains the command `/chuck` is shown below as an example:

```python
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

```

After adding your command you will need to restart tgbot.
## What's next?

I'm planning to integrate [**custom keyboards**](https://core.telegram.org/bots#keyboards), [**inline-mode**](https://core.telegram.org/bots#inline-mode) and **file sending**.

Contributions are welcome.
