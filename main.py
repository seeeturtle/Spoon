import datetime
import parse
import sys
import pprint

def main():
    year, month, day = sys.argv[1:]
    time = datetime.datetime(int(year), int(month), int(day))
    parsed = parse.get_foods(time)
    pprint.pprint(parsed)
    # parse.save_db(parsed, time)


if __name__ == '__main__':
    main()
