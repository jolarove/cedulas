#PAQUETERÍAS
import chromedriver_autoinstaller
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium import webdriver 
from selenium.common.exceptions import TimeoutException
import pandas as pd 
import time 
import logging

#FUNCIONES
def abrirNavegador(website, espera, intentosMaximos, delay, pararCarga):
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
            chromedriver_autoinstaller.install()
            driver = webdriver.Chrome(options=opciones)
            if pararCarga:
                frenarCarga(driver, website)
            else:
                driver.get(website)
            time.sleep(espera)
            return driver
        except Exception as e:
            logger.warning(f'Intento {intento + 1} de {intentosMaximos}, fallido: {e}')
            intento += 1
            time.sleep(delay)
    
    raise Exception(f'No se pudo abrir el navegador después de {intentosMaximos} intentos')

def frenarCarga(driver, website):
    """
    Frena la carga infinita en la página para permitir la extracción (uso para los datos de Estado de México)

    Parámetros:
    driver(WebDriver)
    website(str): web a abrir
    """
    driver.set_page_load_timeout(15)
    try:
        #Carga inicial
        driver.get(website)
    except TimeoutException:
        #Pasado el tiempo, detenemos la carga para poder extraer
        driver.execute_script('window.stop();')
        logger.info('Carga frenada con éxito')

#Configuramos el logger para los mensajes
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

website = 'https://cobupem.edomex.gob.mx/boletines-personas-localizadas'
driver = abrirNavegador(website, 5, 5, 5, True)
html = driver.page_source

datosSubregistro = pd.read_csv('cedulas/Datos/subregistro_desaparecidos_NV.csv')
datosEdoMex = datosSubregistro[datosSubregistro['Estado']=='ESTADO DE MEXICO']
estatus = []
for i, dato in datosEdoMex.iterrows():
    nombre = str(dato['Nombre'])
    print(nombre)
    if nombre in html:
        print('LOCALIZADA')
        estatus.append('LOCALIZADA')
    else:
        estatus.append('BORRADO')
        print('BORRADO')
driver.quit()
datosEdoMex['Estatus'] = estatus
datosEdoMex.to_csv('cedulas/subregistroEdoMex.csv', index=False)