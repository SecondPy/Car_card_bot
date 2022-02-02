from aiogram.types import ReplyKeyboardMarkup, KeyboardButton   #, ReplyKeyboardRemove

b_add_client = KeyboardButton('/Создать_карточку_клиента')
b_delete = KeyboardButton('/Удалить')
b_cancel = KeyboardButton('/Отмена')
b_add_order = KeyboardButton('/Добавить_заказ_наряд')
b_edit_client = KeyboardButton('/Редактировать_карточку_клиента')
b_edit_order = KeyboardButton('/Редактировать_наряд_клиента')
b_yes = KeyboardButton('Да')
b_no = KeyboardButton('Нет')
b_skip = KeyboardButton('Пропустить')


#service buttons
b_e_o = KeyboardButton('Масло моторное')
b_f_f = KeyboardButton('Топливный фильтр')
b_s_p = KeyboardButton('Свечи зажигания')
b_cool = KeyboardButton('Антифриз')
b_cam = KeyboardButton('ГРМ')
b_g_b = KeyboardButton('Масло кпп')
b_b_f = KeyboardButton('Тормозная жидкость')
b_finish = KeyboardButton('Готово')
b_today = KeyboardButton('Сегодня')

#edit client buttons
phone_b = KeyboardButton('Телефон')
licence_b = KeyboardButton('Гос номер')
brand_b = KeyboardButton('Марка авто')
model_b = KeyboardButton('Модель авто')
VIN_b = KeyboardButton('VIN')
b_car = KeyboardButton('Фото авто')

#edit order buttons
mileage = KeyboardButton('Пробег')
cash = KeyboardButton('Стоимость')
date = KeyboardButton('Дату')
des = KeyboardButton('Описание')
rec = KeyboardButton('Рекоммендации')
check = KeyboardButton('Фото наряда')
services = KeyboardButton('ТО (масла, фильтра...)')
back_menu = KeyboardButton('Предыдущее меню')
b_yes, b_no = KeyboardButton('Да'), KeyboardButton('Нет')
back = KeyboardButton('/Назад')


add_or_edit_buttons = ReplyKeyboardMarkup(resize_keyboard=True).row(b_add_client, b_add_order).row(b_edit_client, b_edit_order)
cancel_button = ReplyKeyboardMarkup(resize_keyboard=True).add(b_cancel)
skip_or_cancel_button = ReplyKeyboardMarkup(resize_keyboard=True).row(b_skip, b_cancel)
yes_or_no_buttons = ReplyKeyboardMarkup(resize_keyboard=True).row(b_yes, b_no)
yes_or_no_or_skip_buttons = ReplyKeyboardMarkup(resize_keyboard=True).row(b_yes, b_no, b_skip)
b_today_or_cancel = ReplyKeyboardMarkup(resize_keyboard=True).row(b_today, b_cancel)
edit_client = ReplyKeyboardMarkup(resize_keyboard=True).row(phone_b, licence_b, brand_b).row(model_b, VIN_b, b_car).row(b_finish, b_cancel)
edit_order = ReplyKeyboardMarkup(resize_keyboard=True).row(mileage, cash, date).row(des, rec, check).row(services).row(b_finish, b_cancel)
back_or_cancel = ReplyKeyboardMarkup(resize_keyboard=True).row(back, b_cancel)

service_buttons = ReplyKeyboardMarkup(resize_keyboard=True).row(b_e_o, b_f_f, b_s_p, b_cool)\
                                      .row(b_cam, b_g_b, b_b_f).row(b_finish, b_cancel)

edit_service_buttons = ReplyKeyboardMarkup(resize_keyboard=True).row(b_e_o, b_f_f, b_s_p, b_cool)\
                                          .row(b_cam, b_g_b, b_b_f).row(back_menu, b_finish, b_cancel)