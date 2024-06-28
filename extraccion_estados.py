"""
Usamos la paquetería Selenium junto con time para navegar por las páginas de las comisiones de búsqueda de 
Jalisco, Estado de México, Guanajuato, Puebla, Tabasco y Veracruz para extraer los datos de personas
desaparecidas de las cuales hay cédula de búsqueda oficial.

Utilizamos Pandas para generar las bases de datos extraidas y exportarlas en formato csv

Con logging gestionamos los mensajes de información, alertas, errores, etc.
"""
#PAQUETERÍAS
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium import webdriver 
import pandas as pd 
import time 
import logging

#FUNCIONES
def abrirNavegador(website, espera, intentosMaximos, delay):
    """
    Instala el WebDriver de Chrome
    Abre el navegador Chrome y el sitio especificado con ventana maximizada

    Parámetros:
    website (str): web a abrir
    espera (int): Tiempo de espera en segundos para que abra el sitio
    intentosMaximos (int): Número máximo de intentos para abrir el navegador
    delay (int): Tiempo de espera en segundos entre cada intento

    Retorna: WebDriver
    """    
    opciones = webdriver.ChromeOptions()
    #Si queremos ver el proceso de automatización, comentamos la siguiente línea
    #opciones.add_argument('--headless')
    opciones.add_argument('--start-maximized')
    intento = 0
    while intento < intentosMaximos:
        try:
            servicio = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=servicio, options=opciones)
            driver.get(website)
            time.sleep(espera)
            return driver
        except Exception as e:
            logger.warning(f'Intento {intento + 1} de {intentosMaximos}, fallido: {e}')
            intento += 1
            time.sleep(delay)
    
    raise Exception(f'No se pudo abrir el navegador después de {intentosMaximos} intentos')

#ACCIONES

#Configuramos el logger para los mensajes
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#Definimos variables para el driver
website = 'https://cbpep.puebla.gob.mx/ayudanos-a-encontrarlos'
espera = 5 

#Abrimos el navegador
driver = abrirNavegador(website, espera, 5, 5) 

#Encontramos el total de páginas que tiene el contenedor de las cédulas y lo convertimos a entero
contadorPaginas = driver.find_element(by='xpath', value='//div[@class="k2PaginationCounter"]').text
ultimaPagina = contadorPaginas.split(" ")[-1]
ultimaPagina = int(ultimaPagina)
logger.info(f'En total hay {ultimaPagina} páginas')

#Definimos la variable de la página actual
paginaActual = 1

#Creamos un diccionario con las claves según los datos disponibles para extraer
claves = ['Nombre', 'Url']
diccionarioDatos = {clave: [] for clave in claves}

#Con bucle while navegamos en el contenedor de las cédulas y controlamos la paginación
while paginaActual <= ultimaPagina:
    #Encontramos el contenedor y las cédulas disponibles por página
    contenedor = driver.find_element(by='xpath', value='//div[@class="itemList"]')
    desaparecidos = contenedor.find_elements(by='xpath', value='.//div[@class="catItemBody"]')

    #Con bucle for extraemos la información de cada cédula dentro del contenedor de la página
    for desaparecido in desaparecidos:
        urlImagen = desaparecido.find_element(by='tag name', value='img').get_attribute('src')
        nombre = desaparecido.find_element(by='tag name', value='h3').text

        #Enviamos los datos al diccionario
        diccionarioDatos['Nombre'].append(nombre)
        diccionarioDatos['Url'].append(urlImagen)
        logger.info(f'Registro de {nombre}')
    
    #Con una condicionante damos clic en el botón siguiente, si se está en la última página, no se dará clic
    if paginaActual < ultimaPagina:
        btnSiguiente = driver.find_element(by='xpath', value='//a[@aria-label="Ir a la página siguiente"]')
        driver.execute_script("arguments[0].click();", btnSiguiente)
    #Se actualiza la variable de la página actual
    paginaActual += 1

#Cerramos el navegador
driver.quit()

#Creamos la base de datos
df = pd.DataFrame(diccionarioDatos)

#La exportamos en formato csv
df.to_csv('cedulas/Puebla/desaparecidos_Puebla.csv', index=False)