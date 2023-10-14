from peewee import *

db = SqliteDatabase('database/weather.db')


class Requests(Model):
    """
        Класс таблицы базы данных

        id: id строки
        user_id: id пользователя
        city: город запроса
        date_req: дата запроса
        day_req: дни запросов
        command: команда
    """
    id = AutoField()
    user_id = BigIntegerField()
    city = CharField()
    date_req = DateField()
    day_req = DateField()
    command = CharField()

    class Meta:
        database = db
        db_table = 'requests'
