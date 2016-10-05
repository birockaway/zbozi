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

print "TEST OK"

from pyvirtualdisplay import Display
from selenium import webdriver

display = Display(visible=0, size=(1024, 768))
display.start()

driver= webdriver.Firefox()
driver.get("http://www.somewebsite.com/")

print "got dislpay"

#driver.close() # Close the current window.
driver.quit() # Quit the driver and close every associated window.
display.stop()

print "closed dislpay"