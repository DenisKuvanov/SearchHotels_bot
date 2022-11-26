import telebot
from telebot import types
from search_location import search_city, search_hotels


TOKEN = '5813738796:AAHv8WA1vSu6M2cf7q9PgLOw9nlWqUSoaDE'
bot = telebot.TeleBot(token=TOKEN, parse_mode='HTML')

database = dict()

@bot.message_handler(commands=['start'])
def start(message):
    text = 'Привет, я бот, который быстро подбирает отели по различным ' \
           'критериям поиска\nЧтобы начать мной ползоваться, введи одну из ' \
           'команд, описанных ниже:\n\t/lowprice - подобрать отели по самой ' \
           'низкой цене'
    bot.send_message(message.from_user.id, text)


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.from_user.id, 'Введи /start')


@bot.message_handler(commands=['lowprice'])
def lowprice(message):
    bot.send_message(message.from_user.id, 'Введите название города')
    bot.register_next_step_handler(message, get_city_name)


def get_city_name(message):
    city = message.text
    locations_dct = search_city(city=city)
    menu = types.InlineKeyboardMarkup()
    for loc_name, loc_id in locations_dct.items():
        menu.add(types.InlineKeyboardButton(
            text=loc_name,
            callback_data=loc_id)
        )
    bot.send_message(message.from_user.id, 'Выберете город:',  reply_markup=menu)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    database['city_id'] = call.data
    bot.send_message(call.message.chat.id, 'Укажите дату заезда в формате "дд.мм.гггг"')
    bot.register_next_step_handler(call.message, get_check_in)


def get_check_in(message):
    database['check_in'] = message.text
    bot.send_message(message.from_user.id, 'Укажите дату выезда в формате "дд.мм.гггг"')
    bot.register_next_step_handler(message, get_check_out)


def get_check_out(message):
    database['check_out'] = message.text
    bot.send_message(message.from_user.id, 'Укажите количество взрослых в номере')
    bot.register_next_step_handler(message, get_adults)


def get_adults(message):
    database['adults'] = message.text
    bot.send_message(message.from_user.id, 'Укажите количество детей (если без детей, то укажите 0)')
    bot.register_next_step_handler(message, get_children)


def get_children(message):
    database['children'] = message.text
    bot.send_message(message.from_user.id, 'Введите количество отелей, которые нужно вывести (не больше 20)')
    bot.register_next_step_handler(message, hotels_amount)


def hotels_amount(message):
    database['hotels_amount'] = message.text
    bot.send_message(message.from_user.id, 'Введите количество фото для каждого отеля (если выводить не нужно, то введите 0)')
    bot.register_next_step_handler(message, images_amount)


def images_amount(message):
    database['images_amount'] = message.text
    bot.send_message(message.from_user.id, 'Укажите диапазон цены за сутки в формате "100-200"')
    bot.register_next_step_handler(message, get_price)


def get_price(message):
    database['get_price'] = message.text
    bot.send_message(message.from_user.id, str(database))
    hotels_lst = search_hotels(database)
    for hotel in hotels_lst:
        text = f"Название отеля: {hotel['name']}\nРасстояние до центра: {hotel['distance_from_centre']}\nЦена за сутки: {hotel['price_per_night']}\n" \
               f"Общая сумма: {hotel['total_price']}\nURL адрес отеля: {hotel['url']}"
        bot.send_message(message.from_user.id, text)
        photos = []
        for photo in hotel['images']:
            photos.append(types.InputMediaPhoto(photo))
        if photos:
            bot.send_media_group(message.from_user.id, photos)



# def func():
#     hotels_lst = search_hotels(city_id=call.data)
#     for hotel in hotels_lst:
#         text = f"Название отеля: {hotel['name']}\nРасстояние до центра: {hotel['distance_from_centre']}\nЦена за сутки: {hotel['price_per_night']}\n" \
#                f"Общая сумма: {hotel['total_price']}\nURL адрес отеля: {hotel['url']}"
#         bot.send_message(call.message.chat.id, text)
#         photos = []
#         for photo in hotel['images']:
#             photos.append(types.InputMediaPhoto(photo))
#         bot.send_media_group(call.message.chat.id, photos)








# @bot.message_handler()
# def send_photos(message):
#     photo = []
#     for i in range(3):
#         photo.append(types.InputMediaPhoto(open('C:/Users/denis/PycharmProjects/python_basic_diploma/test_bot/photo.jpg', 'rb')))
#     bot.send_media_group(message.from_user.id, photo)


bot.infinity_polling()