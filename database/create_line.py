from database.db_create import *


def create_line(user_id, city, date_req, days, command) -> None:
    """
        Функция записи истории запросов в базу данных.
        :param user_id: id пользователя
        :param city: город запросов
        :param date_req: дата запроса
        :param days: дни запросов
        :param command: команда запросов
        :return: result
    """
    with db:
        for day in days:
            new_req = Requests(user_id=user_id, city=city, date_req=date_req, day_req=day, command=command).save()
