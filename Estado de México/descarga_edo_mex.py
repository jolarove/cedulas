#Este algoritmo realiza una descarga automática de cédulas de búsqueda de estados de México

#Usamos la biblioteca Selenium para navegar y desvcargar los datos automáticamente
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium import webdriver 
from selenium.common.exceptions import TimeoutException
import pandas as pd 
#Usamos esta librería para las esperas
import time 

#Usamos esta librería para las urls
from urllib.parse import unquote

#Con esta función abrimos la página web en un navegador
#Vamos a darle como atributos la url y el tiempo que queremos esperar
def abrirNavegador(website, espera):    
    opciones = webdriver.ChromeOptions()
    #opciones.add_argument('--headless')
    opciones.add_argument('--start-maximized')
    servicio = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servicio, options=opciones)
    #Hay un error con la página, tiene carga infinita. Por lo tanto, le daremos tiempo para una carga inicial
    driver.set_page_load_timeout(15)
    try:
        #Carga inicial
        driver.get(website)
    except TimeoutException:
        #Pasado el tiempo, detenemos la carga para poder extraer
        driver.execute_script('window.stop();')
    time.sleep(espera)
    return driver

website = 'https://cobupem.edomex.gob.mx/boletines-personas-desaparecidas'
espera = 5
driver = abrirNavegador(website, espera)

#Creamos las listas necesarias
imgUrls = []
nombres = []
meses = []
anios = []
estatus = []

#Buscamos y generamos una lista con todas las cédulas publicadas
#Utilizaremos la url de la imagen para extraer nombre y otra información
imagenesDesaparecidos = driver.find_elements(by='xpath', value='//div[@class="accordion-body"]//img')
  
#Con un bucle for extraemos los datos de cada url encontrada
for imagen in imagenesDesaparecidos:
    try:
        url = imagen.get_attribute('src')
    except:
        url = 'Sin imagen'
    imgUrls.append(url)
    try:
        #Descomponemos la URL para obtener los datos
        nombreUrl = url.split("/")[-1] #Elegimos la parte final de la URL donde está el nombre
        nombreExtension = nombreUrl.split(".")[0] #Eliminamos la extensión después del punto
        nombreFinal = unquote(nombreExtension) #Convertimos los caracteres especiales, por ejemplo espacios
    except:
        nombreFinal = 'Error'
    nombres.append(nombreFinal)
    mes = url.split("/")[-2] #Obtenemos el mes de la URL
    meses.append(mes)
    anio = url.split("/")[-3] #Obtenemos el año de la URL
    anios.append(anio)
    print(nombreFinal) #Print de control
        
driver.quit() #cerramos el navegador

#Creamos la base de datos
df = pd.DataFrame({'Nombre': nombres,
                   'mes': meses,
                   'año': anios,
                   'Url Cédula': imgUrls,})
#Guardamos la base de datos en csv
df.to_csv('cedulas/Estado de Mexico/desaparecidos_cedulas_EdoMex.csv', index=False)

