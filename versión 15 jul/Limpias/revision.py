from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium import webdriver 
from selenium.common.exceptions import TimeoutException
import pandas as pd 
import time 

df = pd.read_csv('cedulas/Limpias/subregistrorevisión.csv',  encoding='latin1')

opciones = webdriver.ChromeOptions()
#Si queremos ver el proceso de automatización, comentamos la siguiente línea
#opciones.add_argument('--headless')
opciones.add_argument('--start-maximized')

servicio = ChromeService(ChromeDriverManager().install())
driver = webdriver.Chrome(service=servicio, options=opciones)

for i, registro in df.iterrows():
    website = str(registro['Url'])
    nombre = str(registro['Nombre'])
    print(nombre)
    driver.get(website)
    time.sleep(2)

driver.quit()

