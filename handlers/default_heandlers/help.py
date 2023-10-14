from telebot.types import Message
from config_data.config import DEFAULT_COMMANDS
from loader import bot


@bot.message_handler(commands=['help'])
def bot_help(message: Message) -> None:
    """
        Команда /help. При вызове команды выводится сообщение с возможностями бота.
        :param message: сообщение пользователя (ввод команды /help).
        :return: None
    """
    text = [f'/{command} - {desk}' for command, desk in DEFAULT_COMMANDS]
    bot.reply_to(message, '\n'.join(text))
