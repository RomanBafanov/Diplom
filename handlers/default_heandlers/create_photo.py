import matplotlib
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


matplotlib.use('agg')


def plotting(day, temp, temp_night) -> None:
    """
        Функция создания графика погоды для команды /custom.
        :param day: дни запросов
        :param temp: дневная температура дней запросов
        :param temp_night: ночная температура дней запросов
        :return: None
    """
    dpi = 80
    fig = plt.figure(dpi=dpi, figsize=(512 / dpi, 384 / dpi))
    mpl.rcParams.update({'font.size': 10})

    plt.title(f'Изменение температуры с {day[0][8:]} по {day[len(day) - 1][8:]}')
    plt.xlabel('Дни')
    plt.ylabel('Температура')

    plt.plot(day, temp, color='red', linestyle='solid', label='Днём',
             marker='o', mec='red', markerfacecolor='black')
    plt.plot(day, temp_night, color='blue', linestyle='solid', label='Ночью',
             marker='o', mec='blue', markerfacecolor='black')
    plt.legend(loc='upper right')
    plt.grid()

    fig.savefig('photo\schedule.png')


def plotting_2(day, temp) -> None:
    """
        Функция создания графика погоды для команд /high и /low.
        :param day: дни запросов
        :param temp: дневная температура дней запросов
        :return: None
    """
    days = np.array(day)
    temps = np.array(temp)

    fig, ax = plt.subplots(figsize=(5, 3))
    ax.stackplot(days, temps, color="y")
    ax.plot(np.zeros(len(day)), color='black', marker='+')
    ax.set_title('Изменение температуры в заданные даты')
    ax.legend(loc='upper left')
    ax.set_ylabel('Температура')
    ax.set_xlabel('Дни')
    ax.grid()
    fig.tight_layout()
    fig.savefig('photo\schedule2.png')

