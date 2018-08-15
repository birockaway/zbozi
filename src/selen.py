# -*- coding: utf-8 -*- 

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException

from keboola import docker # pro komunikaci s parametrama a input/output mapping
from pyvirtualdisplay import Display

import re
import pandas as pd
import os
import time
import datetime
from datetime import date, timedelta # date input
import csv
import sys
import urllib3

print("Python libraries loaded.")

display = Display(visible=0, size=(1024, 768))
display.start()

print("Current Working Directory is ... "+os.getcwd())

print("Config taken from ... "+os.path.abspath(os.path.join(os.getcwd(), os.pardir))+'data/')

# initialize KBC configuration 
##cfg = docker.Config(os.path.abspath(os.path.join(os.getcwd(), os.pardir))+'data/')
# loads application parameters - user defined
##parameters = cfg.get_parameters()

save_path = os.path.abspath(os.path.join(os.getcwd(), os.pardir))+'data/out/tables/'

#creates /data/out/ folder
if not os.path.isdir(save_path):
   os.makedirs(save_path)

#zmeni working directory na slozku, kam se ukladaji statistiky
os.chdir(save_path)

jmeno = 'xxxxxx'
heslo = 'xxxxxx'

start_date = '2018-08-01'
end_date = '2018-08-02'

premise_id = '580'



dates = pd.date_range(start_date, end_date).tolist()
scrape_dates = []
for z in range(len(dates)):
    scrape_dates.append(dates[z].strftime("%Y-%m-%d"))

print("Getting data for following dates: ")
print(scrape_dates)
print("")

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
driver = webdriver.Chrome('/usr/local/bin/chromedriver')

driver.get("https://admin.zbozi.cz/loginScreen?url=%2F")

print("Trying to log in as "+jmeno+" ...")

box_username = driver.find_element_by_name('username')
box_password = driver.find_element_by_name('password')


box_username.send_keys(jmeno)
box_password.send_keys(heslo)
driver.find_element_by_xpath("//input[@type='submit']").click()

time.sleep(1)


if driver.find_elements_by_class_name("pageStatusMessage"):
    print("[ERROR] Failed to log in.")
    print("Invalid email or password. Check the credentials (neplatné přihlášení).")
    driver.quit()
    sys.exit()
else:
    print("Successfully logged in.")
    
for scrape_date in scrape_dates:
    
    print("Getting report for "+scrape_date+" ...")

    date_format = datetime.datetime.strptime(scrape_date, '%Y-%m-%d').strftime('%d.%m.%Y')
    link_web_stats = "https://admin.zbozi.cz/premiseStatistics?premiseId=" + premise_id + "&dateFrom=" + date_format + "&dateTo=" + date_format

    driver.get(link_web_stats)

    # click on Vytvorit novy report
    driver.find_element_by_xpath("//*[@id='new-report-form']/button").click()

    # click on Typ = statistiky polozek
    driver.find_element_by_xpath("//*[@id='new-report-form']/form/div[1]/select/option[2]").click()

    # click on Odeslat a generuj report
    driver.find_element_by_xpath("//*[@id='new-report-form']/form/div[4]/button").click()

    time.sleep(5)
    driver.get(link_web_stats)

    print("["+scrape_date+"] Waiting for the report to be generated... (stav vytváří se)")

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
                     os.rename(filename,"zbozi_stats_"+ scrape_date +".csv")
    
    # rename zbozi_stats.csv to out_zbozi_stats.csv and add scrape_date column to report
    for filename in os.listdir(save_path):
        if filename.endswith(".csv") and not (filename.startswith("out_") or filename.startswith("prior_")):
            with open(save_path+filename,'r',encoding="latin-1") as csvinput:
                with open(save_path+'out_'+filename, 'w') as csvoutput:
                    writer = csv.writer(csvoutput, lineterminator='\n',delimiter=";")
                    reader = csv.reader(csvinput,delimiter=";")
                
                    all = []
                    next(reader,None)
                
                    writer.writerow(['id_polozky','jmeno_polozky','zobrazeni','prokliky','celkova_cena_za_prokliky','pocet_konverzi','scrape_date'])
                
                    for row in reader:
                        row.append(scrape_date)
                        all.append(row)
                
                    writer.writerows(all)
    
    for filename in os.listdir(save_path):
        if not filename.startswith("out_"):
            os.remove(filename)
                
counter = 1
for filename in os.listdir(save_path):
    if filename.startswith("out_"):
        with open(save_path+filename, 'r') as csvinput:
            with open(save_path+'final.csv', 'a') as csvoutput:
                writer = csv.writer(csvoutput, lineterminator='\n',delimiter=";")
                reader = csv.reader(csvinput,lineterminator='\n',delimiter=";")
                all = []
                next(reader,None)
                
                
                
            
                if counter == 1:
                    writer.writerow(['id_polozky','jmeno_polozky','zobrazeni','prokliky','celkova_cena_za_prokliky','pocet_konverzi','scrape_date'])
                
                for row in reader:
                    all.append(row)
                
                writer.writerows(all)
                
                counter = counter + 1

driver.quit()
