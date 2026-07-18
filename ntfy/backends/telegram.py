import asyncio
import configparser
from os import makedirs, path

from appdirs import user_config_dir
from telegram import Bot
from telegram.constants import MessageLimit

config_dir = user_config_dir("ntfy", "dschep")
config_file = path.join(config_dir, "telegram.ini")
MAX_MESSAGE_LENGTH = MessageLimit.MAX_TEXT_LENGTH


def _load_config():
    """Load telegram config, returns (token, chat_id) or None."""
    config = configparser.ConfigParser()
    if not config.read(config_file) or not config.has_section("telegram"):
        return None
    cfg = config["telegram"]
    if "token" not in cfg or "chat_id" not in cfg:
        return None
    chat_id = cfg["chat_id"]
    if chat_id.isdigit():
        chat_id = int(chat_id)
    return cfg["token"], chat_id


async def _interactive_configure():
    """Interactively configure the Telegram bot."""
    prompt = "❯ "
    contact_url = "https://telegram.me/"

    print(
        "Talk with the {} on Telegram ({}), create a bot and insert the token.".format(
            "BotFather", contact_url + "BotFather"
        )
    )

    while True:
        try:
            token = input(prompt).strip()
        except UnicodeEncodeError:
            prompt = "> "
            token = input(prompt).strip()

        try:
            bot = Bot(token)
            me = await bot.get_me()
            print("Connected with {}.\n".format(me.username or me.full_name))
            break
        except Exception as e:
            print("Something went wrong: {}. Please try again.\n".format(e))

    if not path.exists(config_dir):
        makedirs(config_dir)

    config = configparser.ConfigParser()
    config.add_section("telegram")
    config.set("telegram", "token", token)

    print(
        "Enter your Telegram chat/user/channel ID, or the username of the recipient (starting with @):"
    )
    chat_id = input(prompt).strip()
    config.set("telegram", "chat_id", chat_id)

    with open(config_file, "w") as f:
        config.write(f)

    print("Configuration saved to {}\n".format(config_file))


async def _send_message(token, chat_id, text):
    """Send a single message via Telegram Bot API."""
    bot = Bot(token)
    if len(text) > MAX_MESSAGE_LENGTH:
        from warnings import warn

        warn(
            "Message longer than MAX_MESSAGE_LENGTH=%d, splitting into smaller messages."
            % MAX_MESSAGE_LENGTH
        )
        for i in range(0, len(text), MAX_MESSAGE_LENGTH):
            await bot.send_message(
                chat_id=chat_id,
                text=text[i : i + MAX_MESSAGE_LENGTH],
                disable_notification=True,
            )
    else:
        await bot.send_message(chat_id=chat_id, text=text, disable_notification=True)


def notify(title, message, retcode=None):
    cfg = _load_config()
    if cfg is None:
        asyncio.run(_interactive_configure())
        cfg = _load_config()
        if cfg is None:
            raise RuntimeError("Telegram configuration failed")
    token, chat_id = cfg
    asyncio.run(_send_message(token, chat_id, f"{title}\n\n{message}"))
