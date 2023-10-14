from telebot.types import Message
from loader import bot
from database.req_history import *


@bot.message_handler(commands=['history'])
def history(message: Message) -> None:
    """
        Команда /low. При вызове команды выполняется переход в функцию истории.
        :param message: сообщение пользователя (ввод команды /history)
        :return: None
    """
    user_id = message.from_user.id
    result = history_id(user_id)
    bot.send_message(message.chat.id, result)
