# import requests
from lowprice import search_city, search_hotels, print_hotels_info


def main():
    city_id = search_city()
    if not city_id:
        print('Города с таким названием не найдено. Проверьте правильность '
              'ввода города и повторите попытку\n')
    hotels_lst = search_hotels(city_id=city_id)
    print_hotels_info(hotels_lst=hotels_lst)


if __name__ == '__main__':
    main()

