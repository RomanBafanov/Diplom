from telebot.handler_backends import State, StatesGroup

class UserInfo(StatesGroup):
    name = State()
    age = State()
    country = State()
    city = State()
    phone_num = State()
