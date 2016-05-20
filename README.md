# tgbot #

tgbot is another [Telegram](https://telegram.org/) bot written in Python. It's a multipurpose bot that is able to have a conversation (using [ChatterBot](https://github.com/gunthercox/ChatterBot) library), look for trigger keywords in a conversation and launch an automated responses, manage self configuration from Telegram app, it also includes several commands like commands to tell jokes or schedule messages, besides new customs commands can be added pasting python scripts in the commands folder.

## Installation

tgbot needs Python 3.4 or newer to work and it has been tested on OS X 10.9+ and several Debian based systems. It could work over Windows but it has not been tested yet.

First of all you need to create a Telegram bot and get a token, if you don't know how to do it, the process is explained [here](https://core.telegram.org/bots#6-botfather).

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
$sudo update-rc.d tgbot defaults 90 10
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
[Pending section]
<!-- Triggers, admin and other functions) -->
## Custom commands Integration
[Pending section]
<!-- Explanation of custom commands -->

## What's next?

Integration of [**custom keyboards**](https://core.telegram.org/bots#keyboards), [**inline-mode**](https://core.telegram.org/bots#inline-mode) and **file sending**.

Contributions are welcome.
