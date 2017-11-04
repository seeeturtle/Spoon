import re
from bs4 import BeautifulSoup
import psycopg2
import requests
import config

class Food:
    def __init__(self, name=None, stuffs=None):
        self.name = name
        self.stuffs = stuffs

    def __repr__(self):
        return 'Food({self.name!r}, {self.stuffs})'.format(self=self)

def get_foods(time):
    year = time.year
    month = format(time.month, '02d')
    url = (
        'http://stu.goe.go.kr/sts_sci_md00_001.do' 
        '?schulCode=J100006438'
        '&schulCrseScCode=4'
        '&schulKndScCode=04'
        '&schMmealScCode=1'
        '&schYm=') + str(year) + str(month)
    req = requests.get(url)
    return parse_foods(req.text, time)

def parse_foods(text, time):
    soup = BeautifulSoup(text, 'html.parser')
    table = soup.find_all(summary="이 표는 월간 식단에 관한 달력 정보를 제공하고 있습니다.")[0]
    tbody = table.find_all("tbody")[0]
    tds = tbody.find_all("td")
    divs = [td.find("div") for td in tds]
    parsed = [] # type: List[str, List[Food]]
    for div in divs:
        txt = str(div)[5:-6].replace('[중식]<br/>', '').split('<br/>')
        if len(txt) < 3:
            continue
        date = txt[0]
        raw_food = txt[1:]
        foods = []
        for rf in raw_food:
            food = Food()
            splitted = [s for s in re.split('ss|s', rf) if s]
            stuffs = []
            m = re.search('([.]?[0-9]+[.]?)+', splitted[0])
            # check if numbers are in name
            if m:
                raw_foodstuffs = m.group(0)
                stuffs += [int(f) for f in raw_foodstuffs.split('.') if f]
                food.name = splitted[0].replace(raw_foodstuffs, '')
            else:
                food.name = splitted[0]
            # swap &amp; to &
            food.name = food.name.replace('&amp;', '&')
            # remove parentheses
            try:
                food.name = food.name[:food.name.index('(')]
            except:
                pass
            try:
                food.name = food.name[:food.name.index('/')]
            except:
                pass
            if len(splitted) > 1:
                try:
                    raw_foodstuffs = ''
                    for c in splitted[1]:
                        if c == '.' or c.isdigit():
                            raw_foodstuffs += c
                    stuffs += [int(s) for s in raw_foodstuffs.split('.') if s]
                except:
                    print(rf)
            food.stuffs = stuffs
            foods.append(food)
        parsed.append((date, foods))
    return parsed

def save_db(parsed, time):
    conn = psycopg2.connect(dbname=config.DB_NAME, user=config.USER, password=config.PASSWORD, \
            host=config.HOST, port=config.PORT)
    cur = conn.cursor()
    for lunch in parsed:
        date = time.strftime('%Y%m') + '{:02d}'.format(int(lunch[0]))
        cur.execute("select exists(select 1 from lunches where date = %s)", (date,))
        has_data = cur.fetchone()[0]
        if has_data:
            continue
        cur.execute("insert into lunches (date) values (%s) returning lunch_id" , (date,))
        lunch_id = cur.fetchone()[0]
        for food in lunch[1]:
            cur.execute("select exists(select 1 from foods where food_name = %s)", (food.name,))
            has_food = cur.fetchone()[0]
            if has_food:
                cur.execute("select food_id from foods where food_name = %s",
                        (food.name,))
            else:
                cur.execute("insert into foods (food_name, delicious) values (%s, %s) returning food_id",
                        (food.name, is_delicous(food.stuffs)))
            food_id = cur.fetchone()[0]
            if food.stuffs:
                for fs in food.stuffs:
                    cur.execute("insert into foods_foodstuffs (food_id, foodstuff_id) values (%s, %s)", (food_id, fs))
            cur.execute("insert into lunches_foods (lunch_id, food_id) values (%s, %s)", (lunch_id, food_id))
    conn.commit()
    cur.close()
    conn.close()

def is_delicous(foodstuff):
    if foodstuff:
        if 5 in foodstuff and 13 in foodstuff:
            return 't'
        return 'f'
    return 'f'
