from pprint import pprint
from bs4 import BeautifulSoup
import psycopg2
import requests
import datetime
import re
import config

def main():
    time = datetime.datetime.now()
    foods = get_foods(time) # foods is a list of tuples contains food name and food stuff.
    save_db(foods, time)

def get_foods(time):
    year = time.year
    month = format(time.month, '02d')
    url = 'http://stu.goe.go.kr/sts_sci_md00_001.do?schulCode=J100006438&schulCrseScCode=4&schulKndScCode=04&schMmealScCode=1&schYm=' + str(year) + str(month)
    req = requests.get(url)
    return parse_foods(req.text, time)

def parse_foods(text, time):
    soup = BeautifulSoup(text, 'html.parser')
    table = soup.find_all(summary="이 표는 월간 식단에 관한 달력 정보를 제공하고 있습니다.")[0]
    tbody = table.find_all("tbody")[0]
    tds = tbody.find_all("td")
    divs = [td.find("div") for td in tds]
    txts = [div.text for div in divs]
    parsed = []
    for txt in txts:
        if txt != ' ':
            splitted = txt.split('[중식]')
            if len(splitted) > 1:
                parsed.append((str(format(int(splitted[0]), '02d')), splitted[1].replace('s', '')))
    return foods_from_parsed(parsed, time)

def foods_from_parsed(parsed, time):
    foods = []
    for date, foodinfo in parsed:
        a = [m.group(0) for m in re.finditer('[^0-9]+([0-9]+[.])*', foodinfo)]
        a_food = [time.strftime("%Y%m")+date]
        for x in a:
            food = re.match('[가-힣]+', x).group(0)
            pattern = re.compile('([0-9]+[.])+')
            foodstuff = tuple(int(x) for x in pattern.search(x).group(0)[:-1].split('.')) if pattern.search(x) else None
            a_food.append((food, foodstuff))
        foods.append(a_food)
    return foods

def save_db(foods, time):
    conn = psycopg2.connect(dbname=config.DB_NAME, user=config.USER, password=config.PASSWORD, \
            host=config.HOST, port=config.PORT)
    cur = conn.cursor()
    for a_food in foods:
        date = a_food[0]
        cur.execute("select exists(select 1 from lunches where date = %s)", (date,))
        has_data = cur.fetchone()[0]
        if has_data:
            continue
        cur.execute("insert into lunches (date) values (%s) returning lunch_id" , (date,))
        lunch_id = cur.fetchone()[0]
        for food, foodstuff in a_food[1:]:
            cur.execute("select exists(select 1 from foods where food_name = %s)", (food,))
            has_food = cur.fetchone()[0]
            if has_food:
                cur.execute("select food_id from foods where food_name = %s", (food,))
                food_id = cur.fetchone()[0]
            else:
                if foodstuff:
                    cur.execute("insert into foods (food_name, delicious) values (%s, %s) returning food_id",
                            (food, is_delicous(foodstuff)))
                    food_id = cur.fetchone()[0]
            if foodstuff is not None:
                for fs in foodstuff:
                    cur.execute("insert into foods_foodstuffs (food_id, foodstuff_id) values (%s, %s)", (food_id, fs))
            cur.execute("insert into lunches_foods (lunch_id, food_id) values (%s, %s)", (lunch_id, food_id))
    conn.commit()
    cur.close()
    conn.close()

def is_delicous(foodstuff):
    if foodstuff is not None:
        if 5 in foodstuff and 13 in foodstuff:
            return 't'
        return 'f'
    return None

if __name__ == '__main__':
    main()
