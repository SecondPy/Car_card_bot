import string
from sqlalchemy.ext.asyncio import AsyncSession



async def find_phone(text: str): 
    is_phone = text.translate(str.maketrans('', '', string.punctuation)).replace(' ', '') # убираем знаки препинания 
    if len(is_phone) >= 10 and '9' in is_phone:
        nine_index = is_phone.index('9')
        is_phone = is_phone[nine_index:nine_index+10]
        student_phone = is_phone if is_phone.isdigit() and len(is_phone) == 10 else False
        return student_phone
    else: return False