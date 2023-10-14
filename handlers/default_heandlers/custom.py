from typing import Tuple, List, Any
from loguru import logger
from telebot.types import Message
from telebot.handler_backends import State, StatesGroup
from telebot import custom_filters
from loader import bot
from telebot import types
from .search import city_search, direction_search, precipitation_search
from .create_photo import plotting
from database.create_line import create_line
from datetime import datetime
import requests
import json
import re
import os


class MyStates(StatesGroup):
    """
    Класс состояний

    city_custom: состояние 'пользователь ввёл город отслеживания'
    count_day_custom: состояние 'пользователь ввёл дни отслеживания'
    """
    city_custom: State = State()
    count_day_custom: State = State()


params = {}
url = "https://api.weather.yandex.ru/v2/forecast?"
headers = {"X-Yandex-API-Key": "9600755d-a42a-41bc-b63d-879befa3fbae",
           "X-RapidAPI-Host": "https://api.weather.yandex.ru/"}


@bot.message_handler(state=None, commands=['custom'])
def custom_start(message: Message) -> None:
    """
        Команда /custom. При вызове команды запрашивается город отслеживания погоды.
        :param message: сообщение пользователя (ввод команды /custom)
        :return: None
    """
    bot.set_state(message.from_user.id, MyStates.city_custom, message.chat.id)
    bot.send_message(message.chat.id, 'Введите город')


@bot.message_handler(state="*", commands=['cancel'])
def any_state(message) -> None:
    """
        Команда /cancel. При вызове команды останавливается команда /custom.
        :param message: сообщение пользователя (ввод команды /cancel)
        :return: None
    """
    bot.send_message(message.chat.id, "Your state was cancelled.")
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(state=MyStates.city_custom)
def count_day_custom(message) -> None:
    """
        Обработка сообщения пользователя о городе отслеживания погоды.
        Запрашиваются дни отслеживания.
        :param message: сообщение пользователя (город отслеживания погоды)
        :return: None
    """
    bot.send_message(message.chat.id, 'Введите диапазон дней, например 3 6, максимум по 7 день')
    bot.set_state(message.from_user.id, MyStates.count_day_custom, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['city'] = message.text


@bot.message_handler(state=MyStates.count_day_custom)
def low_finish(message) -> None:
    """
        Обработка сообщения пользователя о днях отслеживания погоды.
        Переход в функции запроса данных о погоде и отправки сообщения с результатами.
        :param message: сообщение пользователя (дни отслеживания погоды)
        :return: None
    """
    bot.send_message(message.chat.id, "Загружаю...")
    text = message.text.split()
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['start'] = text[0]
        data['stop'] = text[1]
    lat, lon = city_search(data['city'])
    params['lat'] = lat
    params['lon'] = lon
    params['lang'] = 'ru_RU'
    params['limit'] = '7'
    res, res_2, days = api_request(data)
    send_result(message, res, res_2, data)
    bot.delete_state(message.from_user.id, message.chat.id)
    user_id = message.from_user.id
    date_now = datetime.now().date()
    city = data['city']
    create_line(user_id, city, date_now, days, 'custom')


@logger.catch()
def send_result(message, result, result_2, data) -> None:
    """
        Отправка данных с погодой.
        Переход в функцию с записью запроса в базу данных.
        :param message: None
        :return: None
    """
    markup = types.InlineKeyboardMarkup(row_width=1)
    item1 = types.InlineKeyboardButton(text='Сайт погоды города: {}'.format(data['city']), url=result_2[0])
    markup.add(item1)
    bot.send_message(message.chat.id, result, reply_markup=markup)
    abs_path = os.path.abspath('photo/schedule.png')
    bot.send_photo(message.chat.id, photo=open(abs_path, 'rb'))


@logger.catch()
def api_request(data) -> tuple[str, list[Any], list[Any]] | None:
    """
        Выполняется запрос данных о погоде с Яндекс погода.
        Переход в функцию создания графика изменения погоды в запрашиваемые дни.
        :param message: None
        :return: None
    """
    global result_custom, result_2, days
    try:
        response = requests.request("GET", url, headers=headers, params=params, timeout=10)
        if response.status_code == requests.codes.ok:
            patern = r'url":"(.*?)"'
            result_2 = re.findall(patern, response.text)
            data_2 = json.loads(response.text)
            result_custom = ''
            day_custom = []
            temp = []
            temp_night = []
            days = []
            for num in range(int(data['start']) - 1, int(data['stop'])):
                condition_night = precipitation_search(data_2['forecasts'][num]['parts']['night_short']['condition'])
                condition_day = precipitation_search(data_2['forecasts'][num]['parts']['day_short']['condition'])
                wind_dir_night = direction_search(data_2['forecasts'][num]['parts']['night_short']['wind_dir'])
                wind_dir_day = direction_search(data_2['forecasts'][num]['parts']['day_short']['wind_dir'])
                result_custom += '\nДата: {}'.format(data_2['forecasts'][num]['date'])
                result_custom += '\nНочью:\nМинимальная температура (°C): {temp}' \
                          '\n{condition}' \
                          '\nСкорость ветра (в м/с): {wind_speed}' \
                          '\nСкорость порывов ветра (в м/с): {wind_gust}' \
                          '\nНаправление ветра: {wind_dir}' \
                          '\nДавление (в мм рт. ст.): {pressure_mm}' \
                          '\nВлажность воздуха (в процентах): {humidity}' \
                          '\nПрогнозируемое количество осадков (в мм): {prec_mm}\n'.format(
                    temp=data_2['forecasts'][num]['parts']['night_short']['temp'],
                    condition=condition_night,
                    wind_speed=data_2['forecasts'][num]['parts']['night_short']['wind_speed'],
                    wind_gust=data_2['forecasts'][num]['parts']['night_short']['wind_gust'],
                    wind_dir=wind_dir_night,
                    pressure_mm=data_2['forecasts'][num]['parts']['night_short']['pressure_mm'],
                    humidity=data_2['forecasts'][num]['parts']['night_short']['humidity'],
                    prec_mm=data_2['forecasts'][num]['parts']['night_short']['prec_mm']
                )
                result_custom += '\nДнём:\nТемпература днём (°C) от {temp_min} до {temp}' \
                          '\n{condition}' \
                          '\nСкорость ветра (в м/с): {wind_speed}' \
                          '\nСкорость порывов ветра (в м/с): {wind_gust}' \
                          '\nНаправление ветра: {wind_dir}' \
                          '\nДавление (в мм рт. ст.): {pressure_mm}' \
                          '\nВлажность воздуха (в процентах): {humidity}' \
                          '\nПрогнозируемое количество осадков (в мм): {prec_mm}\n'.format(
                    temp_min=data_2['forecasts'][num]['parts']['day_short']['temp_min'],
                    temp=data_2['forecasts'][num]['parts']['day_short']['temp'],
                    condition=condition_day,
                    wind_speed=data_2['forecasts'][num]['parts']['day_short']['wind_speed'],
                    wind_gust=data_2['forecasts'][num]['parts']['day_short']['wind_gust'],
                    wind_dir=wind_dir_day,
                    pressure_mm=data_2['forecasts'][num]['parts']['day_short']['pressure_mm'],
                    humidity=data_2['forecasts'][num]['parts']['day_short']['humidity'],
                    prec_mm=data_2['forecasts'][num]['parts']['day_short']['prec_mm']
                )
                day_custom.append(data_2['forecasts'][num]['date'])
                temp.append(data_2['forecasts'][num]['parts']['day_short']['temp'])
                temp_night.append(data_2['forecasts'][num]['parts']['night_short']['temp'])
                days.append(data_2['forecasts'][num]['date'])
            plotting(day_custom, temp, temp_night)

        return result_custom, result_2, days
    except Exception:
        return None


bot.add_custom_filter(custom_filters.StateFilter(bot))
