# Это первый мой проект, потенциально имеющий какую-то практическую пользу
# Задумка в том, чтобы клиент СТО всегда имел под рукой историю обслуживания,
# мог быстро записаться на сервис и удобно следить за прохождением регламентного ТО.

# Оно сейчас работает, в будущем добавлю еще несколько функций. Затем займусь оптимизацией и
# приведением в божеский вид согласно Flake8


from aiogram.utils import executor
from create_bot import dp
from data_base import sqlite_db
import os


async def on_startup(_):
    print('Бот вышел в онлайн')
    sqlite_db.sql_start()

from handlers import client, admin, other

admin.register_handlers_admin(dp)
client.register_handlers_client(dp)
other.register_handlers_other(dp)



executor.start_polling(dp, skip_updates=True, on_startup=on_startup)