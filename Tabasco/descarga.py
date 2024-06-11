#Usamos la biblioteca Selenium para navegar y desvcargar los datos automáticamente
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium import webdriver 
import pandas as pd
import time

#Con esta función abrimos la página web en un navegador
#Vamos a darle como atributos la url y el tiempo que queremos esperar
def abrirNavegador(website, espera):    
    opciones = webdriver.ChromeOptions()
    #En esta ocasión, es necesario ocultar el navegador, dado que es un sitio http y no https
    opciones.add_argument('--headless')
    opciones.add_argument('--start-maximized')
    servicio = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servicio, options=opciones)
    driver.get(website)
    time.sleep(espera)
    return driver

website = 'http://busquedadepersonas.tabasco.gob.mx/'

driver = abrirNavegador(website,5) #Abrimos el sitio web

#Buscamos el selector y le especificamos que nos muestre todos los registros en la tabla,
#así evitamos la paginación
selector = driver.find_element(by='xpath', value='//select[@name="dataTable_length"]')
todos = selector.find_element(by='xpath', value='.//option[@value="-1"]')
todos.click()
time.sleep(3)

#Buscamos la tabla y los registros
tabla = driver.find_element(by='id', value='dataTable')
registros = tabla.find_elements(by='xpath', value='.//tbody//tr')

#Creamos las listas
nombresLista = []
sexosLista = []
estadosLista = []
urlsLista = []

#Con un bucle for iteramos entre las filas y columnas para extraer la información y enviarla a las listas
for registro in registros:
    nombres = registro.find_elements(by='xpath', value='.//td[1]')
    sexos = registro.find_elements(by='xpath', value='.//td[2]')
    estados = registro.find_elements(by='xpath', value='.//td[3]')
    urls = registro.find_elements(by='xpath', value='.//td[4]')

    for nombre in nombres:
        nombresLista.append(nombre.text)
        print(nombre.text)
    for sexo in sexos:
        sexosLista.append(sexo.text)
    for estado in estados:
        estadosLista.append(estado.text)
    for url in urls:
        link = url.find_element(by='tag name', value='a').get_attribute('href')
        urlsLista.append(link)

driver.quit() #Cerramos el navegador

#Creamos la base de datos
df = pd.DataFrame({'Nombre': nombresLista,
                   'Sexo': sexosLista,
                   'Estatus': estadosLista,
                   'Url': urlsLista})

#La exportamos en formato csv
df.to_csv('cedulas/Tabasco/desaparecidos_Tabasco.csv', index=False)