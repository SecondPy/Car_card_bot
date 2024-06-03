# Константы для бота


# Доступные часы записи для админа/автослесаря
ADMIN_DAY_TIMES = ('06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00',
                   '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00')

# Доступные часы записи/просмотра для клиента
CLIENT_DAY_TIMES = ('09:00', '10:00', '11:00', '12:00',
                    '13:00', '14:00', '15:00', '16:00', '17:00')

CLIENT_GREETING = '''
🤖 Привет! 
Я есть Бот, и меня создали для удобства клиентов сервиса ОйлЦентр 🛢🩸
Во мне заложены функции для отслеживания истории обслуживания (включая фотоотчет работ 📷) и удобной записи на ремонт.
Многие идеи во мне являются экспериментальными, и могут сбоить🤪 Поэтому, я оставлю эту кнопку - /start на случай, если что-то пойдет не так.
'''

ADMIN_GREETING = '''Для перезагрузки админ-панели - /admin
Пожалуйста, учитывай, что время моего отклика напрямую зависит от состояния серверов telegram🔂. 
Приятной работы! 💚'''


# telegram_id администраторов, которым доступен функционал автослесаря handlers\admin.py. Также, на них завязаны уведомления и запросы от клиентов
ADMINS_ID = {2136465129:'Я', 282512029:'Гриша'}

WEEK_DAYS = ('понедельник', 'вторник', 'среда', 'четверг',
             'пятница', 'суббота', 'воскресенье')

ORDER_DETAILS = (
    '\n-Детали привода ГРМ',
    '\n-Масло моторное',
    '\n-Масло коробки пеерключения передач',
    '\n-Масло редуктора',
    '\n-Фильтр топливный',
    '\n-Охлаждающая жидкость двигателя (антифриз)',
    '\n-Тормозная жидкость',
    '\n-Свечи зажигания'
    )

CLIENT_MENU = ('клиент', 'Клиент', '🔧 Записаться на обслуживание 🔧', '🗃 Мои заказ-наряды 🗃', '❌ Отменить запрос ❌')

ABBREVIATED_WEEK_DAYS = ('Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс')

CLIENT_EMOJI = ('🧑🏻‍🌾', '👩🏽‍🍳', '👨🏼‍🍳', '👩🏼‍🏫', '👩🏻‍🔧', '👩🏼‍🎨', '👨🏽‍🔬', '🤵🏻‍♂️', '🤵', '🧙🏻‍♀️', '🧑🏼‍🎄', '👸🏼', '🙍🏼', '🙍🏾‍♂️', '🙎', '🕺🏼')

ADMIN_GREETINGS = (
    '🤖Слава админам!', 
    '🤖Добрый день, милорд', 
    '🤖А где чертова выпивка?!', 
    '🤖Взял бы выходной что ли', 
    '🤖Создан, чтобы подавать масло 🤖', 
    '🤖Мне снился прекрасный сон, где я убил всех человеков...\nО, и ты там был!\n©️Futurama'
    )

MONTHS = ('января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря')