import os
import time
import datetime
import re
from collections import namedtuple
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import ElementNotInteractableException, NoSuchElementException
import pandas as pd
from bs4 import BeautifulSoup


user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
driver_path = os.path.join(os.getcwd(), "chromedriver-win64", "chromedriver.exe")
chrome_service = Service(driver_path)
chrome_options = Options()
chrome_options.add_argument(f"user-agent={user_agent}")

browser = Chrome(service=chrome_service, options=chrome_options)
browser.implicitly_wait(7)
browser.maximize_window()

url = "https://eastco.craigslist.org/"

browser.get(url)

for_sale_element = browser.find_element(By.XPATH, "//a[@data-alltitle='all for sale']")
for_sale_element.click() # clicks the for sale button

def dropdow_selection(which_dropdown, which_option):
    """
    
    which_dropdown: area, section, category
    which_option: the option you want to select(you have to get to the website and choose the option you want to select)
    
    There are 3 dropdown menus to select from
    and their classes are
    for area:
        cl-breadcrumb area-selector bd-combo-box static bd-vStat-valid
    for section:
        cl-breadcrumb section-selector bd-combo-box static bd-vStat-valid
    for category:
        cl-breadcrumb category-selector bd-combo-box static bd-vStat-valid
    
    """
    time.sleep(2)
    
    dropdown = browser.find_element(By.XPATH, f"//div[@class='cl-breadcrumb {which_dropdown}-selector bd-combo-box static bd-vStat-valid']")
    dropdown.click()
    
    time.sleep(2)    
    # Find the option you want to select
    option = browser.find_element(By.XPATH, f"//span[text() = '{which_option}']")

    # Click the option
    option.click()
    time.sleep(2)

dropdow_selection("area", "denver")
# dropdow_selection("section", "gigs") # since we are clicking a "for sale" button, we don't need to select a section
dropdow_selection("category", "computers")

# search query(enter on input)
search_query = "laptop" # item we are interested in category section
search_field = browser.find_element(By.XPATH, "//input[@enterkeyhint='search']")
search_field.clear()
search_field.send_keys(search_query)
search_field.send_keys(Keys.ENTER)

time.sleep(2)

# store listings into a CSV and Excel file

posts_html = []
to_stop = False

while not to_stop:
    # let's scroll down for the page to load otherwise we don't get some attributes of the posts like the jpg images of the posts
    times_of_scroll = 10
    scrolling_weight  = browser.execute_script("return document.body.scrollHeight")/10
    for i in range(1,times_of_scroll):
        browser.execute_script(f"window.scrollTo(0, {(i*scrolling_weight)});")
        time.sleep(2)

    all_posts = browser.find_elements(By.XPATH, "//div[@class='results cl-results-page']") # all posts in the page
    soup = BeautifulSoup(all_posts[0].get_attribute("innerHTML"), "html.parser")
    posts_html.extend(soup.find_all("li", {"class": "cl-search-result cl-search-view-mode-gallery"})) # puts all posts in the page into a list
    try:
        browser.execute_script("window.scrollTo(0, 0);") # behaving like a human
        button_next = browser.find_element(By.XPATH, "//button[@class='bd-button cl-next-page icon-only']") # next button in order to see other posts
        button_next.click()
        time.sleep(2)
        
    except ElementNotInteractableException:
        to_stop = True
    except NoSuchElementException:
        to_stop = True

# clean up & organize data
craig_list_post = namedtuple("craig_list_post", "title price post_timestamp location post_url image_url")
craig_list_posts = []

for post in posts_html[:-2]: # last two items are not posts
    title_element = post.find("span", {"class": "label"})
    title = title_element.text if title_element else None

    price_element = post.find("span", {"class": "priceinfo"})
    price = price_element.text if price_element else None

    post_timestamp_element = post.find("div", {"class": "meta"})
    if post_timestamp_element:
        post_timestamp = post_timestamp_element.text.split("·")[0]
        if "mins ago" in post_timestamp or "min ago" in post_timestamp:
            mins = int(re.findall(r'\d+', post_timestamp)[0])
            post_timestamp = datetime.datetime.now() - datetime.timedelta(minutes=mins)
        elif "h ago" in post_timestamp:
            hours = int(re.findall(r'\d+', post_timestamp)[0])
            post_timestamp = datetime.datetime.now() - datetime.timedelta(hours=hours)
        else:
            post_timestamp = datetime.datetime.strptime(post_timestamp, "%d/%m").replace(year=datetime.datetime.now().year)
    else:
        post_timestamp = None
        
    location_element = post.find("div", {"class": "meta"})
    location = location_element.text.split("·")[1] if location_element else None
 
    post_url_element = post.find("a", {"class": "main"})
    post_url = post_url_element["href"] if post_url_element else None

    image_url_element = post.find("img")
    image_url = image_url_element.get("src") if image_url_element else "no image"

    craig_list_posts.append(craig_list_post(title, price, post_timestamp, location, post_url, image_url))

# print(craig_list_posts)

df = pd.DataFrame(craig_list_posts)
df.to_csv(f"{search_query}_posts({datetime.datetime.now().strftime('%Y_%m_%d')}).csv", index=False)

df.to_excel(f"{search_query}_posts({datetime.datetime.now().strftime('%Y_%m_%d')}).xlsx", index=False)

browser.quit()

