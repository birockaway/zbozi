import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from keboola import docker # pro komunikaci s parametrama a input/output mapping
import os 
import datetime
from datetime import date, timedelta
import csv
from pyvirtualdisplay import Display

print "Component started."
print "Python libraries loaded."

display = Display(visible=0, size=(1024, 768))
display.start()

print "Current Working Directory is ... "+os.getcwd()

print "Config taken from ... "+os.path.abspath(os.path.join(os.getcwd(), os.pardir))+'data/'

# initialize KBC configuration 
cfg = docker.Config(os.path.abspath(os.path.join(os.getcwd(), os.pardir))+'data/')
# loads application parameters - user defined
parameters = cfg.get_parameters()


### PARAMETERS ####

#date
scrape_date = str(time.strftime("%Y-%m-%d"))

#mode
mode = parameters.get('Mode')
#mode = 'summary'
#mode = 'by_category'
print "Mode is ... "+mode

### DEFINITION OF PARAMETERS ###
#user input - cesta k souboru, kam se maji statistiky ukladat
save_path=os.path.abspath(os.path.join(os.getcwd(), os.pardir))+'data/out/tables/'
#set current date as "today - delta"
delta=2
current_date = str((datetime.datetime.now()-timedelta(delta)).date())

#set stats dates
#date_from = '2016-01-01'
#date_to = '2016-02-16'



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


### /DEFINITION OF PARAMETERS ###
            


#creates /data/out/ folder
if not os.path.isdir(save_path):
   os.makedirs(save_path)

#zmeni working directory na slozku, kam se ukladaji statistiky
os.chdir(save_path)


# To prevent download dialog
profile = webdriver.FirefoxProfile()
profile.set_preference('browser.download.folderList', 2) # custom location
profile.set_preference('browser.download.manager.showWhenStarting', False)
profile.set_preference('browser.download.dir', save_path) # custom location path
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 'text/csv')


#inicializace virtual browseru
def init_driver():
    driver = webdriver.Firefox(profile)
    driver.wait = WebDriverWait(driver, 5)
    return driver
 
#logovaci funkce 
def lookup(driver, query1,query2):
    driver.get("https://admin.zbozi.cz/loginScreen?url=%2F")
    try:
        box_username = driver.wait.until(EC.presence_of_element_located(
            (By.NAME, "username")))
        box_password = driver.wait.until(EC.presence_of_element_located(
            (By.NAME, "password")))   
        box_username.send_keys(query1)
        box_password.send_keys(query2)
        driver.find_element_by_xpath("//input[@type='submit']").click()
    except TimeoutException:
        print("Box or Button not found in google.com")




### BROWSER START FCN ###


def scrape(driver,web_id,shop_shortcut,shop_name,date_from,date_to):
    #check if the dates from and to differs for the by_category extraction
    if mode == 'by_category' and (date_from!=date_to):
        driver.close()
        exit('Error: Extraction query for category view was called while the date_from and date_to differs.')
    if os.path.isfile("out_zbozi_stats_"+shop_shortcut+".csv"):
    #    os.rename("out_zbozi_stats_"+shop_shortcut+".csv","zbozi_stats_"+shop_shortcut+"_"+datetime.datetime.now().isoformat()+".csv")
        os.rename("out_zbozi_stats_"+shop_shortcut+".csv","prior"+"_"+"zbozi_stats_"+shop_shortcut+".csv")    

    # for urls - needs d.m.Y format
    date_from_url = '{d.day}.{d.month}.{d.year}'.format(d=datetime.datetime.strptime(date_from, '%Y-%m-%d'))
    date_to_url = '{d.day}.{d.month}.{d.year}'.format(d=datetime.datetime.strptime(date_to, '%Y-%m-%d'))

    #definice linku pro stahnuti
    link_web_stats = 'https://admin.zbozi.cz/premiseStatistics?premiseId='+web_id+'&dateFrom='+date_from_url+'&dateTo='+date_to_url

    #zavola link na stranku statistik
    driver.get(link_web_stats)
    time.sleep(5)
    try:
        if mode == 'summary':
            # klikni na Vytvorit novy report
            driver.find_element_by_xpath("//*[@id='new-report-form']/button").click()
            
            # klikni na Typ = statistiky polozek
            driver.find_element_by_xpath("//*[@id='new-report-form']/form/div[1]/select/option[2]").click()

        #stickne button na vygenerovani reportu
        driver.find_element_by_xpath("//*[@id='new-report-form']/form/div[4]/button").click()
        
        #pocka 20 sec nez se vygeneruje .csv
        print "Waiting 60 seconds for the report to be generated"
        time.sleep(60)

        #znovu nacte stranku kvuli objeveni odkazu na ztazeni .csv v html
        driver.get(link_web_stats)

        #najde link na ztazeni .csv statistik
        for a in driver.find_elements_by_xpath("//table[@id='statisticsContainer']//tr[3]//td[5]/a"):
    	   link_stats=a.get_attribute('href')

        #proklikne link_stats na stazeni .csv se statistikama
        driver.get(link_stats)

        #w8
        time.sleep(10)


        #prejmenuje .csv soubor poslednich statistik na jednotny nazev, ktery pak pujde do KBC
        for filename in os.listdir(save_path):
            if filename.startswith("statistics"):
                os.rename(filename,"zbozi_stats_"+shop_shortcut+".csv")
        print "Statistics for shop "+shop_name+" has been succesfuly processed."
    except:
        print "(!!!) Statistics for shop "+shop_name+" NOT FOUND on the Zbozi.cz web."
        with open(save_path+"out_zbozi_stats_"+shop_shortcut+".csv", 'w') as csvoutput:
            writer = csv.writer(csvoutput, lineterminator='\n',delimiter=",")
            writer.writerow(['date','clicks','impressions','ctr','cpc_avg','cpc_all','position_avg','conversion_count','conversion_value','converion_rate','conversion_avg_price','scrape_date'])


#predelavac csvcek do slusny podoby
def csv_handeler(mode,stats_date):
    for filename in os.listdir(save_path):
        if filename.endswith(".csv") and not (filename.startswith("out_") or filename.startswith("prior_")):
            with open(save_path+filename,'r') as csvinput:
                with open(save_path+'out_'+filename, 'w') as csvoutput:
                    writer = csv.writer(csvoutput, lineterminator='\n',delimiter=",")
                    reader = csv.reader(csvinput,delimiter=";")

                    all = []

                    if mode == 'summary':
                        next(reader,None)
                        writer.writerow(['date','clicks','impressions','ctr','cpc_avg','cpc_all','position_avg','conversion_count','conversion_value','converion_rate','conversion_avg_price','scrape_date'])

                        for row in reader:
                            row.append(scrape_date)
                            all.append(row)

                    if mode == 'by_category':
                        next(reader,None)
                        writer.writerow(['category_id','category_name','impressions','clicks','cpc_all','conversion_count','date','scrape_date'])
                        for row in reader:
                            row.append(stats_date)
                            row.append(scrape_date)
                            all.append(row)
                    writer.writerows(all)
            #appends the previous table to the new one        
            if (os.path.isfile('prior_'+filename)):
                with open(save_path+'prior_'+filename, 'r') as csvinput:
                    with open(save_path+'out_'+filename, 'a') as csvoutput:
                        writer = csv.writer(csvoutput, lineterminator='\n',delimiter=",")
                        reader = csv.reader(csvinput,lineterminator='\n',delimiter=",")
                        all = []
                        next(reader,None)
                        for row in reader:
                            all.append(row)
                        writer.writerows(all)
                        
                       
    for filename in os.listdir(save_path):
         if not filename.startswith("out_"):
             os.remove(filename)



#inicializuje browser
driver=init_driver()
time.sleep(5)



## SCRAPING

if mode == 'summary':
    date_from=stats_dates[0]
    date_to=stats_dates[len(stats_dates)-1]

    for account_number in range(0,len(parameters.get('Accounts'))):
        # zaloguje usera 
        lookup(driver,parameters.get('Accounts')[account_number].get('Login'), parameters.get('Accounts')[account_number].get('Password'))
        time.sleep(5)

        no_of_shops=len(parameters.get('Accounts')[account_number].get('Shop_name'))

        
        #zavola scraping
        for index in range(0,no_of_shops):
            shop_id = parameters.get('Accounts')[account_number].get('Shop_id')[index]
            shop_shortcut = parameters.get('Accounts')[account_number].get('Shop_shortcut')[index]
            shop_name = parameters.get('Accounts')[account_number].get('Shop_name')[index]
            scrape(driver,shop_id,shop_shortcut,shop_name,date_from,date_to)

    #poresi csvcka
    csv_handeler(mode,date_from)




## /SCRAPING


#zavre browser
driver.close()
display.stop()

time.sleep(5)

os.chdir(save_path)


sample_index=0
try:
    sample_shortcut=parameters.get('Accounts')[0].get('Shop_shortcut')[sample_index]
    print "Sample output:"
    #test print
    cr = csv.reader(open(save_path+"out_zbozi_stats_"+sample_shortcut+".csv","rb"))
    for row in cr:    
        print row
except IOError:
    print "Sample of "+parameters.get('Accounts')[0].get('Shop_name')[sample_index]+" was not avaliable..."
