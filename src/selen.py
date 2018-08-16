# -*- coding: utf-8 -*- 

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

from keboola import docker # pro komunikaci s parametrama a input/output mapping

import re
import pandas as pd
import os
import time
import datetime
from datetime import date, timedelta # date input
import csv
import urllib3
import sys  


import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")

print("Python libraries loaded.")

print("Current Working Directory is ... "+os.getcwd())
print("Config taken from ... "+os.path.abspath(os.path.join(os.getcwd(), os.pardir))+'data/')

# initialize KBC configuration 
cfg = docker.Config(os.path.abspath(os.path.join(os.getcwd(), os.pardir))+'data/')
parameters = cfg.get_parameters()

### PARAMETERS ####
#date
scrape_date = str(time.strftime("%Y-%m-%d"))

login = parameters.get('Login')
password = parameters.get('Password')
shop_id = parameters.get('Shop_id')
eshop_name = parameters.get('Eshop_name')

'''
login = 'test@test'
password = 'pass'
shop_id = '1'
'''

print("Login is "+login)
print("Shop_id is "+shop_id)

### DEFINITION OF PARAMETERS ###
#user input - cesta k souboru, kam se maji statistiky ukladat
save_path = os.path.abspath(os.path.join(os.getcwd(), os.pardir))+'data/out/tables/'
#set current date as "today - delta"
delta=2
current_date = str((datetime.datetime.now()-timedelta(delta)).date())

# date format checker - vyhodi chybu pokud stats_date nebude Y-m-d
def validate(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")

#initialize stats_dates vector
stats_dates={}


#date preset from input parameters. Bud date_preset='Yesteday'/'last_week' nebo vsechny datumy ve stanovenem intervalu
#! parametr 'date_preset' ma prednost.
if parameters.get('Date_preset')=='Yesterday':
    yesterday = date.today() - timedelta(1)
    d1=yesterday
    d2=d1
elif parameters.get('Date_preset')=='last_3_days':
   d1 = date.today() - timedelta(7)
   d2 = date.today() - timedelta(3)
elif parameters.get('Date_preset')=='last_week':
    d1 = date.today() - timedelta(7)
    d2 = date.today() - timedelta(1)
elif parameters.get('Date_preset')=='last_31_days':
    d1 = date.today() - timedelta(31)
    d2 = date.today() - timedelta(1)    
elif parameters.get('Date_preset')=='last_year':
    d1 = date.today() - timedelta(365)
    d2 = date.today() - timedelta(1)
#customdate if not preseted
else:
    validate(parameters.get('Date_from'))
    validate(parameters.get('Date_to'))
    d1=datetime.datetime.strptime(parameters.get('Date_from'),'%Y-%m-%d')
    d2=datetime.datetime.strptime(parameters.get('Date_to'),'%Y-%m-%d')
#vypocet timedelty, ktera urcuje delku tahanych dni zpet    
delta = d2 - d1
for i in range(delta.days+1):
    stats_dates[i]=(d1+timedelta(i)).strftime('%Y-%m-%d')

    
date_from = stats_dates[0]
date_to = stats_dates[len(stats_dates)-1]


# for urls - needs d.m.Y format
date_from_url = '{d.day}.{d.month}.{d.year}'.format(d=datetime.datetime.strptime(date_from, '%Y-%m-%d'))
date_to_url = '{d.day}.{d.month}.{d.year}'.format(d=datetime.datetime.strptime(date_to, '%Y-%m-%d'))

print("Getting data for following date range: " +date_from+ " - " +date_to)

#creates /data/out/ folder
if not os.path.isdir(save_path):
   os.makedirs(save_path)

#zmeni working directory na slozku, kam se ukladaji statistiky
os.chdir(save_path)


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--window-size=1920,1080')

user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5)"
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36")
chrome_options.add_argument('--user-agent={}'.format(user_agent))

#driver = webdriver.Chrome('/usr/local/bin/chromedriver', chrome_options=chrome_options)
driver = webdriver.Chrome(chrome_options=chrome_options)

driver.command_executor._commands["send_command"] = ("POST", '/session/{}/chromium/send_command'.format(driver.session_id))
params = {
            'cmd': 'Page.setDownloadBehavior',
            'params': {'behavior': 'allow', 'downloadPath': save_path}
        }
driver.execute("send_command", params)

driver.get("https://admin.zbozi.cz/loginScreen?url=%2F")

print("Trying to log in as "+login+" with shop_id "+shop_id)

box_username = driver.find_element_by_name('username')
box_password = driver.find_element_by_name('password')


box_username.send_keys(login)
box_password.send_keys(password)
driver.find_element_by_xpath("//input[@type='submit']").click()

time.sleep(1)


if driver.find_elements_by_class_name("pageStatusMessage"):
    print("[ERROR] Failed to log in.")
    print("Invalid email or password. Check the credentials (neplatne prihlaseni).")
    driver.quit()
    sys.exit(1)
else:
    print("Successfully logged in.")
    
for scrape_date in scrape_dates:
    
    print("Getting report for "+scrape_date+" ...")

    date_format = datetime.datetime.strptime(scrape_date, '%Y-%m-%d').strftime('%d.%m.%Y')
    link_web_stats = "https://admin.zbozi.cz/premiseStatistics?premiseId=" + shop_id + "&dateFrom=" + date_from_url + "&dateTo=" + date_to_url

    driver.get(link_web_stats)

    # click on Vytvorit novy report
    driver.find_element_by_xpath("//*[@id='new-report-form']/button").click()

    # click on Typ = statistiky polozek
    driver.find_element_by_xpath("//*[@id='new-report-form']/form/div[1]/select/option[2]").click()

    # click on Odeslat a generuj report
    driver.find_element_by_xpath("//*[@id='new-report-form']/form/div[4]/button").click()

    time.sleep(5)
    driver.get(link_web_stats)

    print("["+scrape_date+"] Waiting for the report to be generated... (stav vytvari se)")

    status = driver.find_elements_by_tag_name("tbody")[0].find_elements_by_tag_name("span")[0].get_attribute('innerHTML')

    while True:
        if status == 'Hotovo':
            break
        else:
            time.sleep(10)
            
            driver.get(link_web_stats)
            status = driver.find_elements_by_tag_name("tbody")[0].find_elements_by_tag_name("span")[0].get_attribute('innerHTML')
        
    link_stats = driver.find_elements_by_partial_link_text("Stáhnout CSV")[0].get_attribute('href')
    
    print("["+scrape_date+"] Report was generated and downloaded.")
    print("")
    driver.get(link_stats)

    time.sleep(2)
    
    # rename statistics_report.csv to zbozi_stats.csv
    for filename in os.listdir(save_path):
                if filename.startswith("statistics"):
                     print("renaming "+filename)
                     os.rename(filename,"zbozi_stats_"+ scrape_date +".csv")
    
    # rename zbozi_stats.csv to out_zbozi_stats.csv and add scrape_date column to report
    for filename in os.listdir(save_path):
        if filename.endswith(".csv") and not (filename.startswith("out_") or filename.startswith("prior_")):
            with open(save_path+filename,'r',encoding="iso-8859-2", errors="ignore") as csvinput:
                with open(save_path+'out_'+filename, 'w',encoding="utf-8") as csvoutput:
                    writer = csv.writer(csvoutput, lineterminator='\n',delimiter=";")
                    reader = csv.reader(csvinput,delimiter=";")
                
                    all = []
                    next(reader,None)
                
                    writer.writerow(['id_polozky','jmeno_polozky','zobrazeni','prokliky','celkova_cena_za_prokliky','pocet_konverzi','date','eshop_name'])
                
                    for row in reader:
                        row.append(scrape_date)
                        row.append(eshop_name)
                        all.append(row)
                
                    writer.writerows(all)
    
    for filename in os.listdir(save_path):
        if not filename.startswith("out_"):
            os.remove(filename)
                
counter = 1
for filename in os.listdir(save_path):
    if filename.startswith("out_"):
        with open(save_path+filename, 'r',encoding="utf-8") as csvinput:
            with open(save_path+'final.csv', 'w',encoding="utf-8") as csvoutput:
                writer = csv.writer(csvoutput, lineterminator='\n',delimiter=",")
                reader = csv.reader(csvinput, delimiter=";")
                all = []
                next(reader,None)

                if counter == 1:
                    writer.writerow(['id_polozky','jmeno_polozky','zobrazeni','prokliky','celkova_cena_za_prokliky','pocet_konverzi','date','eshop_name'])
                
                for row in reader:
                    all.append(row)
                
                writer.writerows(all)
               
                counter = counter + 1

for filename in os.listdir(save_path):
    if not filename.startswith("fin"):
        os.remove(filename)
    
driver.quit()
