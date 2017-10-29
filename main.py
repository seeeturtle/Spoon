import datetime
import parse

def main():
    time = datetime.datetime.now()
    parsed = parse.get_foods(time)
    parse.save_db(parsed, time)


if __name__ == '__main__':
    main()
