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


@bot.message_handler(state=None, commands=['high'])
def high_start(message: Message) -> None:
    """
        Команда /high. При вызове команды запрашивается город отслеживания погоды.
        :param message: сообщение пользователя (ввод команды /high)
        :return: None
    """
    bot.set_state(message.from_user.id, MyStates.city, message.chat.id)
    bot.send_message(message.chat.id, 'Введите город')


@bot.message_handler(state="*", commands=['cancel'])
def any_state(message) -> None:
    """
        Команда /cancel. При вызове команды останавливается команда /high.
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
def high_finish(message) -> None:
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
    res, res_2, days = api_request(data)
    send_result(message, res, res_2, data, days)
    bot.delete_state(message.from_user.id, message.chat.id)


@logger.catch()
def send_result(message, result_high, result_2, data, days) -> None:
    """
        Отправка данных с погодой.
        Переход в функцию с записью запроса в базу данных.
        :param message: None
        :return: None
    """
    markup = types.InlineKeyboardMarkup(row_width=1)
    item1 = types.InlineKeyboardButton(text='Сайт погоды города: {}'.format(data['city']), url=result_2[0])
    markup.add(item1)
    bot.send_message(message.chat.id, result_high, reply_markup=markup)
    abs_path = os.path.abspath('photo/schedule2.png')
    bot.send_photo(message.chat.id, photo=open(abs_path, 'rb'))
    user_id = message.from_user.id
    date_now = datetime.now().date()
    city = data['city']
    create_line(user_id, city, date_now, days, 'high')


@logger.catch()
def api_request(data) -> tuple[str, list[Any], list[Any]] | None:
    """
        Выполняется запрос данных о погоде с Яндекс погода.
        Переход в функцию создания графика изменения погоды в запрашиваемые дни.
        :param message: None
        :return: None
    """
    global result_high, result_2, days
    try:
        response = requests.request("GET", url, params=params, headers=headers, timeout=10)
        if response.status_code == requests.codes.ok:
            patern = r'url":"(.*?)"'
            result_2 = re.findall(patern, response.text)
            data_2 = json.loads(response.text)
            result_high = ''
            day_high = []
            temp = []
            days = []
            for num in range(int(data['count'])):
                condition_night = precipitation_search(data_2['forecasts'][num]['parts']['night_short']['condition'])
                condition_morning = precipitation_search(data_2['forecasts'][num]['parts']['morning']['condition'])
                condition_day = precipitation_search(data_2['forecasts'][num]['parts']['day_short']['condition'])
                condition_evening = precipitation_search(data_2['forecasts'][num]['parts']['day_short']['condition'])
                wind_dir_night = direction_search(data_2['forecasts'][num]['parts']['night_short']['wind_dir'])
                wind_dir_morning = direction_search(data_2['forecasts'][num]['parts']['morning']['wind_dir'])
                wind_dir_day = direction_search(data_2['forecasts'][num]['parts']['day_short']['wind_dir'])
                wind_dir_evening = direction_search(data_2['forecasts'][num]['parts']['evening']['wind_dir'])
                result_high += '\nДата: {}'.format(data_2['forecasts'][num]['date'])
                result_high += '\nНочью:\nМинимальная температура (°C): {temp}' \
                          '\n{condition}' \
                          '\nСкорость ветра (в м/с): {wind_speed}' \
                          '\nСкорость порывов ветра (в м/с): {wind_gust}' \
                          '\nНаправление ветра: {wind_dir}' \
                          '\nДавление (в мм рт. ст.): {pressure_mm}' \
                          '\nВлажность воздуха (в процентах): {humidity}' \
                          '\nПрогнозируемое количество осадков (в мм): {prec_mm}\n'.format(
                    temp=data_2['forecasts'][num]['parts']['night']['temp_min'],
                    condition=condition_night,
                    wind_speed=data_2['forecasts'][num]['parts']['night']['wind_speed'],
                    wind_gust=data_2['forecasts'][num]['parts']['night']['wind_gust'],
                    wind_dir=wind_dir_night,
                    pressure_mm=data_2['forecasts'][num]['parts']['night']['pressure_mm'],
                    humidity=data_2['forecasts'][num]['parts']['night']['humidity'],
                    prec_mm=data_2['forecasts'][num]['parts']['night']['prec_mm']
                )
                result_high += '\nУтром:\nТемпература утром (°C) от {temp_min} до {temp}' \
                          '\n{condition}' \
                          '\nСкорость ветра (в м/с): {wind_speed}' \
                          '\nСкорость порывов ветра (в м/с): {wind_gust}' \
                          '\nНаправление ветра: {wind_dir}' \
                          '\nДавление (в мм рт. ст.): {pressure_mm}' \
                          '\nВлажность воздуха (в процентах): {humidity}' \
                          '\nПрогнозируемое количество осадков (в мм): {prec_mm}\n'.format(
                    temp_min=data_2['forecasts'][num]['parts']['morning']['temp_min'],
                    temp=data_2['forecasts'][num]['parts']['morning']['temp_max'],
                    condition=condition_morning,
                    wind_speed=data_2['forecasts'][num]['parts']['morning']['wind_speed'],
                    wind_gust=data_2['forecasts'][num]['parts']['morning']['wind_gust'],
                    wind_dir=wind_dir_morning,
                    pressure_mm=data_2['forecasts'][num]['parts']['morning']['pressure_mm'],
                    humidity=data_2['forecasts'][num]['parts']['morning']['humidity'],
                    prec_mm=data_2['forecasts'][num]['parts']['morning']['prec_mm']
                )
                result_high += '\nДнём:\nТемпература днём (°C) от {temp_min} до {temp}' \
                          '\n{condition}' \
                          '\nСкорость ветра (в м/с): {wind_speed}' \
                          '\nСкорость порывов ветра (в м/с): {wind_gust}' \
                          '\nНаправление ветра: {wind_dir}' \
                          '\nДавление (в мм рт. ст.): {pressure_mm}' \
                          '\nВлажность воздуха (в процентах): {humidity}' \
                          '\nПрогнозируемое количество осадков (в мм): {prec_mm}\n'.format(
                    temp_min=data_2['forecasts'][num]['parts']['day']['temp_min'],
                    temp=data_2['forecasts'][num]['parts']['day']['temp_max'],
                    condition=condition_day,
                    wind_speed=data_2['forecasts'][num]['parts']['day']['wind_speed'],
                    wind_gust=data_2['forecasts'][num]['parts']['day']['wind_gust'],
                    wind_dir=wind_dir_day,
                    pressure_mm=data_2['forecasts'][num]['parts']['day']['pressure_mm'],
                    humidity=data_2['forecasts'][num]['parts']['day']['humidity'],
                    prec_mm=data_2['forecasts'][num]['parts']['day']['prec_mm']
                )
                result_high += '\nВечером:\nТемпература вечером (°C) от {temp_min} до {temp}' \
                          '\n{condition}' \
                          '\nСкорость ветра (в м/с): {wind_speed}' \
                          '\nСкорость порывов ветра (в м/с): {wind_gust}' \
                          '\nНаправление ветра: {wind_dir}' \
                          '\nДавление (в мм рт. ст.): {pressure_mm}' \
                          '\nВлажность воздуха (в процентах): {humidity}' \
                          '\nПрогнозируемое количество осадков (в мм): {prec_mm}\n'.format(
                    temp_min=data_2['forecasts'][num]['parts']['evening']['temp_min'],
                    temp=data_2['forecasts'][num]['parts']['evening']['temp_max'],
                    condition=condition_evening,
                    wind_speed=data_2['forecasts'][num]['parts']['evening']['wind_speed'],
                    wind_gust=data_2['forecasts'][num]['parts']['evening']['wind_gust'],
                    wind_dir=wind_dir_evening,
                    pressure_mm=data_2['forecasts'][num]['parts']['evening']['pressure_mm'],
                    humidity=data_2['forecasts'][num]['parts']['evening']['humidity'],
                    prec_mm=data_2['forecasts'][num]['parts']['evening']['prec_mm']
                )
                d = '\nночь'
                n = '\nдень'
                day_high.append(data_2['forecasts'][num]['date'][8:] + d)
                day_high.append(data_2['forecasts'][num]['date'][8:] + n)
                temp.append(data_2['forecasts'][num]['parts']['night']['temp_min'])
                temp.append(data_2['forecasts'][num]['parts']['day']['temp_min'])
                days.append(data_2['forecasts'][num]['date'])
            plotting_2(day_high, temp)

        return result_high, result_2, days
    except Exception:
        return None


bot.add_custom_filter(custom_filters.StateFilter(bot))