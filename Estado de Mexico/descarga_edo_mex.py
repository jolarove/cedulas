#Este algoritmo realiza una descarga automática de cédulas de búsqueda de estados de México

#Usamos la biblioteca Selenium para navegar y desvcargar los datos automáticamente
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium import webdriver 
import pandas as pd 
#Usamos esta librería para las esperas
import time 

#Con las siguientes librerías descargamos las imágenes
import requests 
from PIL import Image
from io import BytesIO

from unidecode import unidecode #para eliminar acentos
import re
from urllib.parse import urlparse, unquote

#Con esta función abrimos la página web en un navegador
#Vamos a darle como atributos la url y el tiempo que queremos esperar
def abrirNavegador(website, espera):    
    opciones = webdriver.ChromeOptions()
    #opciones.add_argument('--headless')
    opciones.add_argument('--start-maximized')
    servicio = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servicio, options=opciones)
    driver.get(website)
    time.sleep(espera)
    return driver

website = 'https://cobupem.edomex.gob.mx/boletines-personas-desaparecidas'
espera = 5
driver = abrirNavegador(website, espera)


imagenesDesaparecidos = driver.find_elements(by='xpath', value='//div[@class="accordion-body"]//img')
imgUrls = []
nombres = []
meses = []
anios = []
for imagen in imagenesDesaparecidos:
    try:
        url = imagen.get_attribute('src')
    except:
        url = 'Sin imagen'
    imgUrls.append(url)
    try:
        nombreUrl = url.split("/")[-1]
        nombreExtension = nombreUrl.split(".")[0]
        nombreFinal = unquote(nombreExtension)
    except:
        nombreFinal = 'Error'
    nombres.append(nombreFinal)
    mes = url.split("/")[-2]
    meses.append(mes)
    anio = url.split("/")[-3]
    anios.append(anio)
    print(nombreFinal)




driver.quit()

df = pd.DataFrame({'Nombre': nombres,
                   'mes': meses,
                   'año': anios,
                   'Url Cédula': imgUrls})
df.to_csv('cedulas/Estado de Mexico/desaparecidos_cedulas_EdoMex.csv', index=False)

