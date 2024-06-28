from const_values import ADMINS_ID


async def which_admin(tg_id):
    if tg_id in ADMINS_ID: return ADMINS_ID[tg_id]
    else: return tg_id