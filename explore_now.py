from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from database import config as dbcfg
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import time
import os
import bs4

#Access to the 'Explore' page
path = "https://www.explore.org/livecams/explore-all-cams/"

# Use Firefox/Chrome to access the page
executable_path = os.getcwd()+'/crawler/webdriver/geckodriver'
driver = webdriver.Firefox(executable_path=executable_path)
driver.get(path)
e = driver.switch_to.active_element

timeout = 30
try:
    element_present = EC.presence_of_element_located((By.ID, 'video-carousel'))
    WebDriverWait(driver, timeout).until(element_present)
    time.sleep(1)
except TimeoutException as e:
    print(e)

# To retrieve a list of images from the 'explore', print each page element value from the homepage and save it as a list.
id_element = driver.find_element_by_id('video-carousel')
sour = id_element.get_attribute('innerHTML')[1:]
pour = sour
ptr = sour.find('href')
li = []
li2 = []

#soup = bs4.BeautifulSoup('html.parser')
soup = bs4.BeautifulSoup(driver.page_source,'html.parser')
cam_list = soup.find(id='video-carousel').find_all('div',{'class':'cam-container'})
for cam in cam_list:
    if ('is-online' in cam['class']) or ('is-offline' in cam['class']):
        li.append(cam.findChild()['href'])
        li2.append(cam.findChild()['data-cam-id'])

# Connect to pymysql
import pymysql

con = pymysql.connect(dbcfg.HOSTNAME, dbcfg.USERNAME, dbcfg.PASSWORD, dbcfg.DATABASE)
cur = con.cursor()
exe = 'select * from enf_source'

# Extract m3u8 using the list stored in the list
URL_m3u8 = []
for k, i in enumerate(li2):
    m3u8 = 'https://outbound-production.explore.org/stream-production-' + i + '/.m3u8'
    URL_m3u8.append(m3u8)

# Load each image page using the list and extract location information (latitude, longitude) stored in str form from the source code.
#driver = webdriver.Firefox(executable_path=executable_path)
for k, i in enumerate(li):
    try:
        URL = 'https://www.explore.org' + i
        print(URL)

        driver.get(URL)
        #time.sleep(8)
        try:
            element_present = EC.presence_of_element_located((By.CLASS_NAME, 'plr-10'))
            WebDriverWait(driver, timeout).until(element_present)
        except TimeoutException as e:
            print('Timeout')
            print(e)
            continue

        class_element = driver.find_element_by_class_name('plr-10')
        code = class_element.get_attribute('innerHTML')
        pt = code.find('center')
        code2 = code[pt+len('center='):]
        pt2 = code2.find('&')
        var2 = code2[:pt2]
        l = var2.split(',') # (latitude, longitude)

        id_element2 = driver.find_element_by_id('cam-name')
        code2 = id_element2.get_attribute('innerHTML')
        pt2 = code2.find('cam-location')

        id_element2 = driver.find_element_by_id('cam-name')
        code3 = id_element2.get_attribute('innerHTML')
        pt2 = code3.find('u-font-foundation-light')
        code4 = code3[pt2+len('u-font-foundation-light'):]
        var3 = code4[2:code4.find('</span>')]

        #driver.quit()

        # Store each extracted element in sql information
        sql = "INSERT INTO enf_source(service_uid, source_name, url, url_m3u8, latitude, longitude) VALUES (%s, %s, %s, %s, %s, %s)"

        cur.execute(sql, ('3', var3, URL, URL_m3u8[k], l[0], l[1]))
        con.commit()

    except:
        print('problem occured in: '+URL)
        continue
