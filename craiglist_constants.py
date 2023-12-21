import os
import time
import datetime
import re
import json
from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

def remove_digits_from_string(input_string):
    return input_string.translate(str.maketrans('', '', '0123456789'))

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
driver_path = os.path.join(os.getcwd(), "chromedriver-win64", "chromedriver.exe")
chrome_service = Service(driver_path)
chrome_options = Options()
chrome_options.add_argument(f"user-agent={user_agent}")

browser = Chrome(service=chrome_service, options=chrome_options)
browser.implicitly_wait(7)
browser.maximize_window()

url = "https://www.craigslist.org/about/sites"
browser.get(url)

time.sleep(2)
us_element = browser.find_element(By.XPATH, "//div[@class='colmask']")
soup = BeautifulSoup(us_element.get_attribute("innerHTML"), "html.parser")

# let's get the states and cities into a dictionary
state_city_dict = {}
states = soup.find_all('h4')
city_lists = soup.find_all('ul')



for state, city_list in zip(states, city_lists):
    state_name = state.text
    city_dict_list = []
    cities = city_list.find_all('li')
    for city in cities:
        city_name = city.text
        city_url = city.find('a')['href']
        city_dict_list.append({city_name: city_url})
    state_city_dict[state_name] = city_dict_list

os.makedirs('constants_json', exist_ok=True)

with open(f'constants_json/state_cities({datetime.datetime.now().strftime("%Y_%m_%d")}).json', 'w') as f:
    json.dump(state_city_dict, f)

time.sleep(4)

browser.get("https://albuquerque.craigslist.org/") # go to albuquerque craigslist albuequerque is actually random all we are interested in is the categories that 
               # craigslist show for every city


all_categories = browser.find_elements(By.XPATH, "//div[@class='cats']")

categories_dict = {}
for category in all_categories[:-1]:
    # let's get the ul ids 
    category_id = category.find_element(By.TAG_NAME, 'ul').get_attribute("id")
    category_id = remove_digits_from_string(category_id)
    categories_dict[category_id] = category.text.split("\n")

# write to file
with open(f'constants_json/categories({datetime.datetime.now().strftime("%Y_%m_%d")}).json', 'w') as f:
    json.dump(categories_dict, f)
    
browser.quit()