from aiogram.types import ReplyKeyboardMarkup, KeyboardButton   #, ReplyKeyboardRemove


b1 = KeyboardButton('Мой автомобиль')
b2 = KeyboardButton('Мои заказ-наряды')
b3 = KeyboardButton('Рекоммендации')

b4 = KeyboardButton('/Поделиться номером телефона', request_contact=True)
b_allow = KeyboardButton('Разрешить')
b_mute = KeyboardButton('Запретить')
b_skip = KeyboardButton('Пропустить')
b_order = KeyboardButton('Записаться на сервис/шиномонтаж/схождение...')

b_cancel_state = ('/Выход')
#b5 = KeyboardButton('Отправить где я', request_location=True)
kb_reg = ReplyKeyboardMarkup(resize_keyboard=True)
kb_permission = ReplyKeyboardMarkup(resize_keyboard=True)
kb_client = ReplyKeyboardMarkup(resize_keyboard=True)
kb_cancel_state = ReplyKeyboardMarkup(resize_keyboard=True)
kb_cancel_or_skip = ReplyKeyboardMarkup(resize_keyboard=True)

kb_reg.row(b4)
kb_permission.row(b_allow, b_mute)
kb_client.row(b1, b2, b3).add(b_order)
kb_cancel_state.add(b_cancel_state)
kb_cancel_or_skip.row(b_skip, b_cancel_state)
