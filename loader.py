from telebot import TeleBot
import telebot
from telebot.storage import StateMemoryStorage
from config_data import config

state_storage = StateMemoryStorage()


bot = telebot.TeleBot(config.BOT_TOKEN, state_storage=state_storage)
