from telebot.types import Message
from loader import bot


@bot.message_handler(commands=['hello_world'])
def bot_start(message: Message) -> None:
    """
        Команда /hello_world. При вызове команды бот приветствует мир!.
        :param message: сообщение пользователя (ввод команды /hello_world)
        :return: None
    """
    bot.reply_to(message, "Привет мир!")