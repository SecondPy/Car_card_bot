import json
ar = []

with open('cenz.txt', 'r') as r:
    for i in r:
        n = i.lower().split(', ')
        if n != '':
            with open ('cenz.json', 'w', encoding='utf-8') as e:
                json.dump(n, e)
