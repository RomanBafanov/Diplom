from telebot.types import Message
from loader import bot
from telebot import types


@bot.message_handler(commands=['start'])
def bot_start(message: Message) -> None:
    """
    Команда /start. При вызове команды запускается бот и приветствуется пользователь.
    :param message: сообщение пользователя (ввод команды /start)
    :return: None
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('/start')
    item2 = types.KeyboardButton('/help')
    item3 = types.KeyboardButton('/hello_world')
    item4 = types.KeyboardButton('/low')
    item5 = types.KeyboardButton('/high')
    item6 = types.KeyboardButton('/custom')
    item7 = types.KeyboardButton('/history')

    markup.add(item1, item2, item3, item4, item5, item6, item7)

    bot.reply_to(message, f"Привет, {message.from_user.full_name}!\n"
                          f"\nЯ бот погоды! Со мной ты можешь:\n"
                          f"- узнать погоду в выбранном городе днём и ночью\n   (команда /low)\n"
                          f"- более подробную информацию погоды на день\n   (команда /high)\n"
                          f"- погоду в определённый отрезок дней\n   (команда /custom)\n"
                          f"- а так же историю своих запросов!\n   (команда /history)\n"
                          f"Выбрав команду /help, можно более подробно узнать о моих возможностях!\n"
                          f"\nПриятного пользования!", reply_markup=markup)
