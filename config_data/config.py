import os
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    exit('Переменные окружения не загружены т.к отсутствует файл .env')
else:
    load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
DEFAULT_COMMANDS = (
    ('start', "Запустить бота"),
    ('hello_world', "Поздароваться с миром"),
    ('help', "Вывести справку"),
    ('low', "Погода ночью и днём"),
    ('high', "Погода ночью, утром, днём и вечером"),
    ('custom', "Погода ночью и днём в диапазоне нескольких дней"),
    ('history', "История запросов")
)
