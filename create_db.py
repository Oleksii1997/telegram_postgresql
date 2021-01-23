import binary as binary
from selenium import webdriver
import psycopg2
import psycopg2.extras

# chromedriver для selenium
CHROMEDRIVER_PATH = '/home/oleksiy/myproject/telegram_db/selenium_db_bot/chromedriver'
# дані для підключення до бд postgresql
DB_NAME = ''  # ваші дані
DB_USER = ''  # ваші дані
DB_PASS = ''  # ваші дані
DB_HOST = ''  # ваші дані


# зберігаємо в бд області та відповідні url отримані функцією region_parse()
def region_save_db(region_list):
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor()
    # # створюємо бд областей
    # cur.execute("CREATE TABLE Region"
    #            "(id int NOT NULL PRIMARY KEY,"
    #            "region_name varchar(255) NOT NULL,"
    #            "region_url varchar(700))")

    id_n = 1
    for region in region_list:
        name = region["region_name"]
        url = region["region_url"]
        cur.execute("INSERT INTO Region (id, region_name, region_url) "
                    f"VALUES ({id_n}, '{name}', '{url}')")
        conn.commit()
        id_n += 1
    cur.close()
    conn.close()


# отримуємо назви областей та url відповідних сторінок
def region_parse():
    driver = webdriver.Chrome(executable_path=f'{CHROMEDRIVER_PATH}')
    driver.get("https://sinoptik.ua/украина")
    div_region = driver.find_element_by_class_name("jspPane")
    regions = div_region.find_elements_by_tag_name('a')
    regions_list = []
    for region in regions:
        region_dict = {'region_url': region.get_attribute('href'), 'region_name': region.get_attribute('text')}
        regions_list.append(region_dict)
    return regions_list


# збираємо та зберігаємо області та url в бд Postgrsql
def get_region():
    region_list = region_parse()
    region_save_db(region_list)


# отримуємо та зберігаємо в бд райони та відповідні url
def district_save_db():
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    '''
    # створюємо бд районів
    cur.execute("CREATE TABLE District"
                "(id_district int NOT NULL PRIMARY KEY,"
                "region integer REFERENCES Region(id),"
                "district_name varchar(255) NOT NULL,"
                "district_url varchar(700) NOT NULL)")
    '''
    cur.execute("SELECT * FROM Region")
    regions = cur.fetchall()
    id_district = 1
    for region in regions:
        region_id = region["id"]
        region_name = region["region_name"]
        region_url = region["region_url"]
        district_data = district_parse(region_url)
        print(f"{region_name} \n")
        for district in district_data:
            name = district["district_name"]
            url = district["district_url"]
            cur.execute("INSERT INTO District (id_district, region, district_name, district_url) "
                        f"VALUES ({id_district}, {region_id}, '{name}', '{url}')")
            conn.commit()
            id_district += 1
        print("OK \n")

    conn.commit()

    cur.close()
    conn.close()


def district_parse(region_url):
    driver = webdriver.Chrome(executable_path=f'{CHROMEDRIVER_PATH}')
    driver.get(f"{region_url}")
    div_district = driver.find_element_by_class_name("jspPane")
    districts = div_district.find_elements_by_tag_name('a')
    district_list = []
    for district in districts:
        district_dict = {'district_url': district.get_attribute('href'),
                         'district_name': district.get_attribute('text')}
        district_list.append(district_dict)
    return district_list


def get_district():
    district_save_db()


# отримуємо та зберігаємо в бд населені пункти та відповідні url
def city_save_db():
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # створюємо бд міст
    '''
    cur.execute("CREATE TABLE City"
                "(id_city int NOT NULL PRIMARY KEY,"
                "district integer REFERENCES District(id_district),"
                "city_name varchar(255) NOT NULL,"
                "city_url varchar(700) NOT NULL)")
    '''

    cur.execute("SELECT * FROM District")
    districts = cur.fetchall()
    id_city = 1
    for district in districts:
        district_url = district["district_url"]
        district_name = district["district_name"]
        district_id = district["id_district"]
        city_data = city_parse(district_url)
        for city in city_data:
            name = city["city_name"]
            url = city["city_url"]
            cur.execute("INSERT INTO City (id_city, district, city_name, city_url) "
                        f"VALUES ({id_city}, {district_id}, '{name}', '{url}')")
            conn.commit()
            id_city += 1
        print(f"{district_name} - OK")

    conn.commit()

    cur.close()
    conn.close()


def city_parse(district_url):
    driver = webdriver.Chrome(executable_path=f'{CHROMEDRIVER_PATH}')
    driver.get(f"{district_url}")
    div_city = driver.find_element_by_class_name("mapBotCol")
    cities_div = div_city.find_elements_by_class_name('clearfix')[0]
    cities = cities_div.find_elements_by_tag_name('a')
    city_list = []
    for city in cities:
        city_dict = {'city_url': city.get_attribute('href'),
                     'city_name': city.get_attribute('text')}
        city_list.append(city_dict)
    return city_list


def get_city():
    city_save_db()


if __name__ == '__main__':
    # get_region()
    # get_district()
    get_city()

