import locale
from datetime import date, datetime, timedelta


from const_values import WEEK_DAYS, MONTHS

locale.setlocale(locale.LC_TIME, 'Russian')




class DateFormatter:
    def __init__(self, date_time: datetime):
        
        
        today = datetime.today().date()
        if date_time == today:
            self.date_num = 'Сегодня'
        else: self.date_num = str(int(date_time.strftime('%d')))

        if date_time.strftime('%B') in ('Март', 'Август'):
            self.month = f"{date_time.strftime('%d %B').lower()+'а'}, ({WEEK_DAYS[date_time.weekday()]})"
        else: 
            self.month = f"{date_time.strftime('%d %B').replace('ь', 'я').replace('й', 'я').lower()} ({WEEK_DAYS[date_time.weekday()]})"
        if self.month[0] == '0': self.month = self.month.replace('0', '')
        self.time = date_time.strftime('%H:%M') if date_time.strftime('%H:%M') != '00:00' else ''
        
        self.message_format = f'{self.month} {self.time}'
