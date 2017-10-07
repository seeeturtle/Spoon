from pprint import pprint
from bs4 import BeautifulSoup
import requests
import datetime
import re

def main():
    time = datetime.datetime.now()
    foods = get_foods(time) # foods is a list of tuples contains food name and food stuff.
    pprint(foods)

def get_foods(time):
    year = time.year
    month = format(time.month, '02d')
    url = 'http://stu.goe.go.kr/sts_sci_md00_001.do?schulCode=J100006438&schulCrseScCode=4&schulKndScCode=04&schMmealScCode=1&schYm=' + str(year) + str(month)
    req = requests.get(url)
    return parse_foods(req.text)

def parse_foods(text):
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
                parsed.append((int(splitted[0]), splitted[1].replace('s', '')))
    return foods_from_parsed(parsed)

def foods_from_parsed(parsed):
    foods = []
    for _, foodinfo in parsed:
        a = [m.group(0) for m in re.finditer('[^0-9]+([0-9]+[.])*', foodinfo)]
        for x in a:
            food = re.match('[가-힣]+', x).group(0)
            pattern = re.compile('([0-9]+[.])+')
            foodstuff = tuple(int(x) for x in pattern.search(x).group(0)[:-1].split('.')) if pattern.search(x) else None
            foods.append((food, foodstuff))
    return foods

if __name__ == '__main__':
    main()
