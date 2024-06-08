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

def cerrar(btn):
    btnCerrar = driver.find_element(by='xpath', value=btn)
    btnCerrar.click()
    time.sleep(2)


def descargarImagen(url, descarga, nombre, lista, estado):
        try:
            img = requests.get(url)
            print(url)
            if img.status_code == 200 and img.headers.get("content-type", "").startswith("image"):
                imagen = Image.open(BytesIO(img.content)) 
                imagen.save(f'cedulas/{estado}/imagenes/{nombre}.png')
                lista.append(True)
            else:
                lista.append(descarga)
        
        except:
            lista.append(descarga)
            print('error')
        return lista

website = 'https://www.segobver.gob.mx/cebv/busqueda_personas3.php'
espera = 5
driver = abrirNavegador(website, espera)

btn = '//button[@class="btn btn-outline-secondary"]'
cerrar(btn)

nombre = []
fecha = []
imgUrl = []
estatusLista = []

estatusSelector = driver.find_elements(by='xpath', value='//select[@id="idArea"]//option')
for estatus in estatusSelector:
    estatus.click()
    estado = estatus.text
    print(estado)
    time.sleep(1)
    btnBuscar = driver.find_element(by='xpath', value='//button[@onclick="buscar1()"]')
    btnBuscar.click()
    time.sleep(3)

    contenedor = driver.find_element(by='xpath', value='//div[@id="contenedor"]')
    
    #Encontramos el total de elementos en la tabla, lo usaremos para la paginación
    textoDetalles = contenedor.find_element(by='xpath', value='.//div[@class="details"]//span').text
    totalCasos = re.search(r'de (\d+) registros', textoDetalles)
    if totalCasos:
        totalCasos = int(totalCasos.group(1))
        print(totalCasos)
    else:
        print('Hubo un error')
        break
    elementosCapturados = 0
    print(elementosCapturados)
    while elementosCapturados < totalCasos:
        tabla = driver.find_element(by='id', value='tblResult')
        casos = tabla.find_elements(by='xpath', value='.//tbody//tr')
        for caso in casos:
            nombres = caso.find_elements(by='xpath', value='.//td[1]')
            fechas = caso.find_elements(by='xpath', value='.//td[2]')
            imagenes = caso.find_elements(by='xpath', value='.//td[3]')

            for elemento in nombres:
                nombre.append(elemento.text)
                if estado == 'No localizadas':
                    estatusLista.append('Desaparecido')
                else:
                    estatusLista.append('Localizado')
                elementosCapturados += 1
                print(f'{elemento.text} {elementosCapturados}')
            for elemento in fechas:
                fecha.append(elemento.text)
            for elemento in imagenes:
                try:
                    imagen = elemento.find_element(by='xpath', value='.//a').get_attribute('href')
                except:
                    imagen = 'Sin imagen'
                imgUrl.append(imagen)

        #Paginación
        if elementosCapturados < totalCasos:
            btnSiguiente = driver.find_element(by='xpath', value='//div[contains(text(), "Sig")]')
            try:
                btnSiguiente.click()
            except:
                driver.execute_script("arguments[0].click();", btnSiguiente)
            time.sleep(1)
        
driver.close()

df = pd.DataFrame({'Nombre': nombre,
                   'Fecha desaparición': fecha,
                   'Url imagen': imgUrl,
                   'Estatus': estatusLista})

df.to_csv('cedulas/Veracruz/desaparecidos_Veracruz.csv', index=False)