from telebot.types import Message
from loader import bot


@bot.message_handler(content_types=['text'])
def get_text(message) -> None:
    """
        Отслеживание вводимого приветствия пользователем.
        :param message: сообщение пользователя (приветствие).
        :return: None
    """
    if message.text.lower() == 'привет':
        bot.reply_to(message, f"И тебе {message.from_user.full_name} привет!")


@bot.message_handler(state=None)
def bot_echo(message: Message):
    """
        Отслеживание вводимого текста вне команд бота. Работает в виде echo.
        :param message: сообщение пользователя.
        :return: None
    """
    bot.reply_to(message, "Эхо без состояния или фильтра.\nСообщение:"
                          f"{message.text}")
