from database.db_create import *


def history_id(id) -> str:
    """
        Функция создания истории запросов.
        :param id: id пользователя
        :return: result
    """
    v = Requests.select().where(Requests.user_id == id)
    result = 'История запросов:\n'
    city = ''
    for n in v:
        if city != n.city:
            result += '\n\nГород: {city}  ' \
                      'Дата запроса: {date_req}  ' \
                      'Команда: {command}  ' \
                      '\nДни запросов: {day_req},\t'.format(
                city=n.city,
                date_req=str(n.date_req),
                command=n.command,
                day_req=str(n.day_req))
            city = n.city
        else:
            result += '{day_req},\t'.format(day_req=str(n.day_req))

    return result
