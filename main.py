import datetime
from pprint import pprint
import parse

def main():
    time = datetime.datetime.now()
    parsed = parse.get_foods(time)
    pprint(parsed)


if __name__ == '__main__':
    main()
