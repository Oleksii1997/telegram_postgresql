import telebot
from telebot import types
from geopy.geocoders import Nominatim
import requests
from bs4 import BeautifulSoup
import psycopg2
import psycopg2.extras
import emoji

HOST = 'https://sinoptik.ua/'
URL = 'https://sinoptik.ua/погода-'
HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/'
              'avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.367.36'
}

# дані для підключення до бази даних postgresql
DB_NAME = ''  # ваші дані
DB_USER = ''  # ваші дані
DB_PASS = ''  # ваші дані
DB_HOST = ''  # ваші дані

SELECT_CITY_BUTT = emoji.emojize("Обрати населений пункт :globe_showing_Europe-Africa: :Ukraine:")
GET_LOCATION_BUTT = emoji.emojize("Надіслати геолокацію :satellite:")

# токен бота
bot = telebot.TeleBot('1495859171:AAHTqpbBMwxbnbavD5r5Jus779lBp94rRvw', parse_mode=None)


# обробка команд надісланих боту
@bot.message_handler(commands=['start', 'help', 'about'])
def start_func(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
    geolocation = types.KeyboardButton(text=f"{GET_LOCATION_BUTT}", request_location=True)
    select_city = types.KeyboardButton(text=f"{SELECT_CITY_BUTT}")
    markup.row(geolocation)
    markup.row(select_city)
    if message.text == '/start':
        text = emoji.emojize("Привіт) :victory_hand:\n"
                             "Уведіть назву населеного пункту :globe_showing_Europe-Africa: :Ukraine:"
                             ", погода в якому вас цікавить, :sun: "
                             "відправте геолокацію :satellite: або оберіть населений пункт "
                             "зі списку :bookmark_tabs:")
    elif message.text == '/help':
        text = emoji.emojize("Привіт) :victory_hand:\n Я можу показати вам погоду :sun_behind_small_cloud: "
                             "за певний період часу :calendar:, якщо ви надішлете мені свою геолокацію "
                             ":satellite:, або назву міста :Ukraine:. Також ви можете "
                             "обрати населений пункт зі списку :magnifying_glass_tilted_left:, для цього натисніть на "
                             "кнопку 'Обрати населений пункт':page_with_curl:\n Щоб запустити або почати заново наш "
                             "діалог відправте команду '/start' :repeat_button:")
    else:
        text = emoji.emojize("Привіт) :victory_hand: Я бот :snake: який вміє позувати погоду "
                             ":sun_behind_small_cloud: :sun:.\n"
                             "Для того щоб почати діалог зі мною надішліть команду '/start'\n"
                             "Далі я запропоную відправити мені ваше місцезнаходження :satellite: або назву "
                             "населеного пункут :globe_showing_Europe-Africa: :Ukraine:, погоду в якому ви хочете "
                             "дізнатися.\n Я перевірю :thinking_face: чи таке місто існує, і якщо ви мене не "
                             "намагаєтесь надурити :smiling_face_with_sunglasses:, \n"
                             "зберу для вас погоду :sun_with_face: за обраний період часу.\n"
                             "Необхідну інформацію мені надає сайт sinoptik.ua :thumbs_up:")
    bot.send_message(message.chat.id, f"{text}", reply_markup=markup)


# обробка тексту надісланого користувачем, бот очікує отримати назву міста, перевіряє і видає результат
@bot.message_handler(content_types=['text'])
def get_geolocation(message):
    if message.text == f"{SELECT_CITY_BUTT}":
        select_city = SelectCity(message)
        select_city.get_region()
    else:
        bot_geo = GetLocation(message)
        bot_geo.city_name_valid()


# отримуємо геолокацію користувача
@bot.message_handler(content_types=['location'])
def get_geolocation(message):
    bot_geo = GetLocation(message)
    bot_geo.search_location()


# обробка клавіатури вибору дня на який цікавить погода
@bot.callback_query_handler(func=lambda message: inline_wether_valid(message))
def select_wether(message):
    data = message.data.split(',')
    bot_pars = ParsWeather(message)
    if data[2] == 'text':  # від клавіатури коли клієнт вводив назву населеного пункту
        bot_pars.get_html()
    elif data[2] == 'db_id':  # якщо клієнт обирає назву населеного пункту з бази даних
        id_city = int(message.data.split(',')[0])
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(f"SELECT * FROM City WHERE id_city={id_city}")
        city = cur.fetchall()
        city_url = f"{city[0]['city_url']}/10-дней"
        r = requests.get(f"{city_url}")
        if len(city) == 1 and r.status_code is 200:
            bot_pars.get_content(r)
        else:
            bot_pars.page_error()


# обробка клавіатури вибору області
@bot.callback_query_handler(func=lambda message: inline_region_valid(message))
def select_region(message):
    select_city = SelectCity(message)
    select_city.get_district()


# обробка клавіатури вибору району
@bot.callback_query_handler(func=lambda message: inline_district_valid(message))
def select_region(message):
    select_city = SelectCity(message)
    select_city.get_city()


# обробка клавіатури вибору населеного пункту
@bot.callback_query_handler(func=lambda message: inline_city_valid(message))
def get_weather(message):
    city_obj = SelectCity(message)
    city_obj.days_weather_db()


# перевірка, що відповідь саме від клавіатури вибору дня погоди
def inline_wether_valid(message):
    try:
        data = message.data.split(',')
        if int(data[1]) in [1, 3, 7, 10]:
            return True
        else:
            return False
    except IndexError:
        return False


# перевірка, що відповідь саме від клавіатури вибору області
def inline_region_valid(message):
    try:
        data = message.data.split('_')
        if data[0] == 'region':
            return True
        else:
            return False
    except IndexError:
        return False


# перевірка, що відповідь саме від клавіатури вибору району
def inline_district_valid(message):
    try:
        data = message.data.split('_')
        if data[0] == 'district':
            return True
        else:
            return False
    except IndexError:
        return False


# перевірка, що відповідь саме від клавіатури вибору населеного пункту
def inline_city_valid(message):
    try:
        data = message.data.split('_')
        if data[0] == 'city':
            return True
        else:
            return False
    except IndexError:
        return False


# клас який працює з об'єктом геолокації та текстом, назвою міста, який надісланий боту
# перевіряє чи існує відповідна сторінка на sinoptik.ua
# повертає користувачу повідомлення помилки або клавіатуру вибору дати погоди
class GetLocation:
    def __init__(self, message):
        self.message = message
        self.error_location = emoji.emojize("Сталася помилка :police_car_light:, об'єкт геолокації не надав необхідну "
                                            "інформацію :compass: Надішліть текстову назву населеного пункту.")
        self.city_name_error = emoji.emojize(":warning:Перевірте правильність написання, такий "
                                             "населений пункт не знайдено :compass:")

    # надсилає користувачу повідомлення про помилку
    def search_error(self, error_message):
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        geolocation = types.KeyboardButton(text=f"{GET_LOCATION_BUTT}", request_location=True)
        select_city = types.KeyboardButton(text=f"{SELECT_CITY_BUTT}")
        markup.row(geolocation)
        markup.row(select_city)
        bot.send_message(self.message.chat.id, f'{error_message}', reply_markup=markup)

    # надсилає клавіатуру вибору днів погоди
    def days_weather(self, city_name):
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(text=f"Погода, {city_name}, на сьогодні", callback_data=f"{city_name},1,text"))
        keyboard.add(
            types.InlineKeyboardButton(text=f"Погода, {city_name}, на 3 дні", callback_data=f"{city_name},3,text"))
        keyboard.add(
            types.InlineKeyboardButton(text=f"Погода, {city_name}, на 7 днів", callback_data=f"{city_name},7,text"))
        keyboard.add(
            types.InlineKeyboardButton(text=f"Погода, {city_name}, на 10 днів", callback_data=f"{city_name},10,text"))
        bot.send_message(self.message.chat.id, "Погода на який день вас цікавить?", reply_markup=keyboard)

    # перевірка чи об'єкт геолокації повернув назву населеного пункту і
    # чи існує відповідна сторінка на sinoptik.ua
    # повертає або помилку або клавіатуру
    def city_sinoptic_valid(self, geo_list):
        city_name = None
        for item in geo_list:
            if " " in item or item.isdigit() or item == 'Україна':
                pass
            else:
                r = requests.get(f"{URL}{item}", headers=HEADERS)
                if r.status_code is 200:
                    city_name = item
        if city_name is None:
            if len(geo_list) > 1:
                self.search_error(self.error_location)
            else:
                self.search_error(self.city_name_error)
        else:
            self.days_weather(city_name.capitalize())

    # якщо користувач надіслав геолокацію, отримуємо адресу з об'єкта геолокації
    # повертає або помилку або викликає city_sinoptic_valid(self, geo_list)
    def search_location(self):
        geolocator = Nominatim(user_agent='weather.py')
        # якщо ми отримали геолокацію
        try:
            location_list = geolocator.reverse(
                "%s, %s" % (str(self.message.location.latitude), str(self.message.location.longitude)),
                timeout=3, exactly_one=True)
        except:
            location_list = None
        if location_list is not None:
            location_list = location_list.address.split(', ')
            self.city_sinoptic_valid(location_list)
        else:
            self.search_error(self.error_location)

    # якщо користувач надіслав текстову назву міста, перевіряємо валідність
    # повертає або помилку або викликає city_sinoptic_valid(self, geo_list)
    def city_name_valid(self):
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        geolocation = types.KeyboardButton(text=f"{GET_LOCATION_BUTT}", request_location=True)
        select_city = types.KeyboardButton(text=f"{SELECT_CITY_BUTT}")
        markup.row(geolocation)
        markup.row(select_city)
        chars = set('0123456789$,@?!^";:-+=#№<>*/|')
        if any((c in chars) for c in self.message.text):
            text = emoji.emojize(":warning:Назва населеного пункту не повинна містити символів або чисел")
            bot.send_message(self.message.chat.id, f"{text}", reply_markup=markup)
        elif ' ' in self.message.text:
            text = emoji.emojize(":warning:В назві не повинно бути пробілів, напишіть через дефіс")
            bot.send_message(self.message.chat.id, f"{text}", reply_markup=markup)
        elif len(self.message.text) >= 45:
            text = emoji.emojize(":warning:Такого населеного пункту не існує")
            bot.send_message(self.message.chat.id, f"{text}", reply_markup=markup)
        else:
            geo_list = [self.message.text.lower()]
            self.city_sinoptic_valid(geo_list)


# клас який збирає погоду за запитом клієнта і надає відповідь
class ParsWeather:

    def __init__(self, message):
        self.message = message

    # повідомлення про помилку якщо сторінка sinoptik.ua не відповідає
    def page_error(self):
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        geolocation = types.KeyboardButton(text=f"{GET_LOCATION_BUTT}", request_location=True)
        select_city = types.KeyboardButton(text=f"{SELECT_CITY_BUTT}")
        markup.row(geolocation)
        markup.row(select_city)
        bot.send_message(self.message.message.chat.id, "Сталася помилка(, спробуйте пізніше. ", reply_markup=markup)

    # відправляємо результат клієнту
    def view_weather(self, data_list, city_name=None, region=None):
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True, one_time_keyboard=True)
        geolocation = types.KeyboardButton(text=f"{GET_LOCATION_BUTT}", request_location=True)
        select_city = types.KeyboardButton(text=f"{SELECT_CITY_BUTT}")
        markup.row(geolocation)
        markup.row(select_city)
        result_text = emoji.emojize(
            f"Я зібрав інформацію :thermometer: за вашим запитом :OK_hand:.\n "
            f":world_map:{city_name} \n {region} \n\n"
        )
        for item in data_list:
            result_text += emoji.emojize(
                f':calendar:{item["date"]} {item["month"]}: \n   Макс :hot_face:{item["max_temp"]} - '
                f'Мін :cold_face: {item["min_temp"]} \n   :open_book:{item["description"]}\n\n')
        bot.send_message(self.message.message.chat.id, f"{result_text}", reply_markup=markup)

    # парсимо дані з сторінки, викликаємо view_weather або page_error
    def get_content(self, r):
        item = 1
        days = int(self.message.data.split(',')[1])  # на скільки днів потрібно показувати погоду
        soup = BeautifulSoup(r.content, 'html.parser')
        try:
            city_name = soup.find('div', class_='cityName').find('h1').text
            region = soup.find('div', class_='currentRegion').text
            data_list = []
            while item <= days:
                data_dict = {}
                if item == 1:
                    data_dict["description"] = soup.find('div', class_='wDescription').find('div',
                                                                                            class_='description').text

                else:
                    data_dict["description"] = soup.find('div', id=f'bd{item}').find('div', class_='weatherIco').get(
                        'title')
                data_dict["max_temp"] = soup.find('div', id=f'bd{item}').find('div', class_='max').find('span').text
                data_dict["min_temp"] = soup.find('div', id=f'bd{item}').find('div', class_='min').find('span').text
                data_dict["date"] = soup.find('div', id=f'bd{item}').find('p', class_='date').text
                data_dict["month"] = soup.find('div', id=f'bd{item}').find('p', class_='month').text
                data_list.append(data_dict)
                item += 1
            self.view_weather(data_list, city_name, region)
        except:
            self.page_error()

    # отримуємо сторінку html, передаємо її парсеру, або викликаємо помилку
    def get_html(self):
        city_name = self.message.data.split(',')[0].lower()
        r = requests.get(f"{URL}{city_name}/10-дней")
        if r.status_code is 200:
            self.get_content(r)
        else:
            self.page_error()


# для ручного варіанту вибора населеного пункту з бази даних Postgresql
class SelectCity:

    def __init__(self, message):
        self.message = message

    # отримуємо з бд список областей та відображаємо клавіатуру
    def get_region(self):
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT * FROM Region")
        regions = cur.fetchall()
        keyboard = types.InlineKeyboardMarkup()
        for region in regions:
            keyboard.add(types.InlineKeyboardButton(text=f"{region['region_name']}",
                                                    callback_data=f"region_{region['id']}"))
        text = emoji.emojize("Оберіть область :world_map:")
        bot.send_message(self.message.chat.id, f"{text}", reply_markup=keyboard)
        cur.close()
        conn.close()

    # отримуємо з бд список районів та відображаємо клавіатуру
    def get_district(self):
        id_region = int(self.message.data.split('_')[1])  # id області
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(f"SELECT * FROM District WHERE region={id_region}")
        districts = cur.fetchall()
        keyboard = types.InlineKeyboardMarkup()
        for district in districts:
            keyboard.add(types.InlineKeyboardButton(text=f"{district['district_name']}",
                                                    callback_data=f"district_{district['id_district']}"))
        text = emoji.emojize("Оберіть район :world_map:")
        bot.send_message(self.message.message.chat.id, f"{text}", reply_markup=keyboard)
        cur.close()
        conn.close()

    # отримуємо з бд список населенх пунктів та відображаємо клавіатуру
    def get_city(self):
        id_district = int(self.message.data.split('_')[1])  # id району
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(f"SELECT * FROM City WHERE district={id_district}")
        cities = cur.fetchall()
        keyboard = types.InlineKeyboardMarkup()
        for city in cities:
            keyboard.add(types.InlineKeyboardButton(text=f"{city['city_name']}",
                                                    callback_data=f"city_{city['id_city']}"))
        text = emoji.emojize("Оберіть населений пункт :world_map:")
        bot.send_message(self.message.message.chat.id, f"{text}", reply_markup=keyboard)
        cur.close()
        conn.close()

    # надсилає клавіатуру вибору днів погоди
    def days_weather_db(self):
        id_city = int(self.message.data.split('_')[1])  # id міста
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(f"SELECT * FROM City WHERE id_city={id_city}")
        city = cur.fetchall()
        if len(city) == 1:
            city_name = city[0]["city_name"]
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton(text=f"Погода, {city_name}, на сьогодні", callback_data=f"{id_city},1,db_id"))
            keyboard.add(
                types.InlineKeyboardButton(text=f"Погода, {city_name}, на 3 дні", callback_data=f"{id_city},3,db_id"))
            keyboard.add(
                types.InlineKeyboardButton(text=f"Погода, {city_name}, на 7 днів", callback_data=f"{id_city},7,db_id"))
            keyboard.add(
                types.InlineKeyboardButton(text=f"Погода, {city_name}, на 10 днів",
                                           callback_data=f"{id_city},10,db_id"))
            bot.send_message(self.message.message.chat.id, "Погода на який день вас цікавить?", reply_markup=keyboard)
        else:
            error = ParsWeather(self.message)
            error.page_error()


if __name__ == "__main__":
    bot.polling()
