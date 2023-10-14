from typing import Tuple, List, Any
from loguru import logger
from telebot.types import Message
from telebot import custom_filters
from loader import bot
from telebot import types
from .search import city_search, direction_search, precipitation_search, MyStates
from .create_photo import plotting_2
from database.create_line import create_line
from datetime import datetime
import requests
import json
import re
import os


params = {}
url = "https://api.weather.yandex.ru/v2/forecast?"
headers = {"X-Yandex-API-Key": "9600755d-a42a-41bc-b63d-879befa3fbae",
           "X-RapidAPI-Host": "https://api.weather.yandex.ru/"}


@bot.message_handler(state=None, commands=['low'])
def low_start(message: Message) -> None:
    """
        Команда /low. При вызове команды запрашивается город отслеживания погоды.
        :param message: сообщение пользователя (ввод команды /low)
        :return: None
    """
    bot.set_state(message.from_user.id, MyStates.city, message.chat.id)
    bot.send_message(message.chat.id, 'Введите город')


@bot.message_handler(state="*", commands=['cancel'])
def any_state(message) -> None:
    """
        Команда /cancel. При вызове команды останавливается команда /low.
        :param message: сообщение пользователя (ввод команды /cancel)
        :return: None
    """
    bot.send_message(message.chat.id, "Your state was cancelled.")
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(state=MyStates.city)
def count_day(message) -> None:
    """
        Обработка сообщения пользователя о городе отслеживания погоды.
        Запрашиваются дни отслеживания.
        :param message: сообщение пользователя (город отслеживания погоды)
        :return: None
    """
    bot.send_message(message.chat.id, 'Введите кол-во дней для просмотра погоды, максимально 7 дней')
    bot.set_state(message.from_user.id, MyStates.count_day, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['city'] = message.text


@bot.message_handler(state=MyStates.count_day)
def low_finish(message) -> None:
    """
        Обработка сообщения пользователя о днях отслеживания погоды.
        Переход в функции запроса данных о погоде и отправки сообщения с результатами.
        :param message: сообщение пользователя (дни отслеживания погоды)
        :return: None
    """
    bot.send_message(message.chat.id, "Загружаю...")
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['count'] = int(message.text)
    lat, lon = city_search(data['city'])
    params['lat'] = lat
    params['lon'] = lon
    params['lang'] = 'ru_RU'
    params['limit'] = data['count']
    result, result_2, days = api_request(data)
    send_result(message, result, result_2, data, days)
    bot.delete_state(message.from_user.id, message.chat.id)


@logger.catch()
def send_result(message, result, result_2, data, days) -> None:
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
    abs_path = os.path.abspath('photo/schedule2.png')
    bot.send_photo(message.chat.id, photo=open(abs_path, 'rb'))
    user_id = message.from_user.id
    date_now = datetime.now().date()
    city = data['city']
    create_line(user_id, city, date_now, days, 'low')


@logger.catch()
def api_request(data) -> tuple[str, list[Any], list[Any]] | None:
    """
        Выполняется запрос данных о погоде с Яндекс погода.
        Переход в функцию создания графика изменения погоды в запрашиваемые дни.
        :param message: None
        :return: None
    """
    global result, result_2, days
    try:
        response = requests.request("GET", url, params=params, headers=headers, timeout=10)
        if response.status_code == requests.codes.ok:
            patern = r'url":"(.*?)"'
            result_2 = re.findall(patern, response.text)
            data_2 = json.loads(response.text)
            result = ''
            day = []
            temp = []
            days = []
            for num in range(int(data['count'])):
                condition_night = precipitation_search(data_2['forecasts'][num]['parts']['night_short']['condition'])
                condition_day = precipitation_search(data_2['forecasts'][num]['parts']['day_short']['condition'])
                wind_dir_night = direction_search(data_2['forecasts'][num]['parts']['night_short']['wind_dir'])
                wind_dir_day = direction_search(data_2['forecasts'][num]['parts']['day_short']['wind_dir'])
                result += '\nДата: {}'.format(data_2['forecasts'][num]['date'])
                result += '\nНочью:\nМинимальная температура (°C): {temp}' \
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
                result += '\nДнём:\nТемпература днём (°C) от {temp_min} до {temp}' \
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
                d = '\nночь'
                n = '\nдень'
                day.append(data_2['forecasts'][num]['date'][8:] + d)
                day.append(data_2['forecasts'][num]['date'][8:] + n)
                temp.append(data_2['forecasts'][num]['parts']['night_short']['temp'])
                temp.append(data_2['forecasts'][num]['parts']['day_short']['temp_min'])
                days.append(data_2['forecasts'][num]['date'])
            plotting_2(day, temp)

        return result, result_2, days
    except Exception:
        return None


bot.add_custom_filter(custom_filters.StateFilter(bot))
