import sys
from datetime import datetime

from py_cz_api import Token
from py_cz_api import Api

from dadata import Dadata

# Словари для читабельности
ki_type = {'UNIT': 'КИЗ', 'BOX': 'КИТУ', 'GROUP': 'КИГУ'}
prod_group = {'water': 'Упакованная вода', 'beer': 'Пиво', 'softdrinks': 'Напитки'}
statuses = {'INTRODUCED': 'В обороте', 'RETIRED': "Выведен из оборота",
            'EMITTED': 'Не введён в оборот', 'DISAGGREGATION': 'Расформирован', 'WRITTEN_OFF': 'КИГУ разобран'}
owners = {'9108118124': 'ООО ДФ РУСЛАНА', '9102154817': 'АО ПБКК', '9201520366': 'ООО ДФ РУСЛАНА ПЛЮС'}


def read_token():
    # чтение токена из файла
    try:
        with open("token.txt", "r") as file:
            return Token(file.read())
    except FileNotFoundError:
        print("Ошибка: Файл не найден.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def get_result_from_api(cis):
    # возврат dict от TrueAPI
    return api.cises_short_list(cis)[0]


def date_convert(date: str):
    # конвертация из строки в объект Date
    return datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%fZ")


def get_prod_date(res: dict):        # Получение даты розлива в зависимости от типа КИ
    if res.get('extendedPackageType') == 'UNIT':
        return date_convert(res.get('producedDate'))
    elif res.get('packageType') == 'LEVEL1':
        return date_convert(get_result_from_api(res.get('children')).get('producedDate'))
    elif res.get('packageType') == 'LEVEL2':
        return date_convert(get_result_from_api(get_result_from_api(res.get('children')).get('children')).get('producedDate'))
    else:
        return "00-00-00T00:00:00Z"


api = Api(read_token())

cis_list = ['02046100172504882100208062508552891']        # КИЗ Пиво КЕГ
result = get_result_from_api(cis_list)

if not len(result.get('gtin')):     # проверка на валидность марки
    print("Такой марки не существует")
    sys.exit()

# Вывод необходимых данных из ответа
print(f"Марка: {result.get('cis')}")
print(f"Группа: {prod_group.get(result.get('productGroup'))}")

gt_res = api.gtin_info([(result.get('gtin'))]).get('results')[0]        # Получаем инфу по GTIN
print(gt_res.get('fullName'))

if gt_res.get('packageType') == 'КЕГ':      # Печать объёма, если кег
    print(gt_res.get('consumerPackageVolume'))

print(f"Тип кода: {ki_type.get(result.get('extendedPackageType'))}")
print(f"Статус: {statuses.get(result.get('status'))}")
if result.get('status') == "EMITTED":
    sys.exit()
print(f"Дата розлива: {get_prod_date(result).strftime('%d.%m.%Y')}")

if result.get('status') == 'RETIRED':       # Опциональный вывод времени и причины вывода по выведенным из оборота
    print(f"Дата и время вывода из оборота: {date_convert(result.get('receiptDate')).strftime('%d.%m.%Y %H:%M')}")
    print(f"Причина вывода: {result.get('withdrawReason')}")

# Получение данных об организации по ИНН (через сервис DADATA)
inn_token = "0584d318862ae69f75b82c35ceaaaac202143d23"
dadata = Dadata(inn_token)
print(f"Владелец: {dadata.find_by_id('party', result.get('ownerInn'))[0].get('value')}")

if result.get('status') == 'INTRODUCED' and 'parent' in result:     # Вывод предка, если существует
    print(f"Входит в состав: {result.get('parent')}")

if result.get('extendedPackageType') != 'UNIT':     # Вывод вложений, если КИТУ или КИГУ
    print("Содержит вложения: ")
    for i in result.get('children'):
        print(i)

if result.get('productGroup') == "beer" and gt_res.get('packageType') == 'КЕГ':
    if result.get('statusEx') == 'CONNECT_TAP':
        print(f"Поставлено на кран: {date_convert(result.get('connectDate')).strftime('%d.%m.%Y %H:%M')}")
        print(f"Срок годности после подключения: до {date_convert(result.get('expirations')[1].get('expirationStorageDate')).strftime('%d.%m.%Y')}")
    else:
        print("Ещё не поставлено на кран")
    if 'soldCount' in result.get('specialAttributes'):
        print(f"Реализовано: {int(result.get('specialAttributes').get('soldCount')) / 1000} литров")

# for i in result.keys():
#     print(f"{i} это {result.get(i)}")
