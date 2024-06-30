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

#Configuramos el logger para los mensajes
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

website = 'https://busquedageneralizada.gob.mx/consulta/'
espera = 5

driver = abrirNavegador(website, espera, 5, 5)

claves = ['Nombre','Folio', 'Categoría', 'Estatus']
datosDesaparecidos = {clave: [] for clave in claves}

desaparecidosBorrados = pd.read_csv('cedulas/Datos/desaparecidos_borrados.csv')

for i, desaparecido in desaparecidosBorrados.iterrows():
    inputBusqueda = driver.find_element(by='xpath', value='//input[@type="search"]')
    inputBusqueda.clear()
    nombre = str(desaparecido["Nombre"])
    estado = str(desaparecido['Estado'])
    datosDesaparecidos['Nombre'].append(nombre)
    logger.info(f'Rastreando caso de: {nombre}')
    inputBusqueda.send_keys(nombre)
    time.sleep(1)
    tabla = driver.find_element(by='tag name', value='table')
    filas = tabla.find_elements(by='xpath', value='.//tbody//tr')

    datos = filas[0].find_elements(by='tag name', value='td')
    campos = [dato.text for dato in datos]

    def encontrarEstatus(estatus, campos, diccionario):
        if estatus == 'borrado':
            folio = 'SIN DATO'
            categoria = 'SIN DATO'
            estatusDic = 'BORRADO'
            logger.info(f'El caso de {nombre} fue borrado')
        elif estatus == 'invisibilizado':
            folio = campos[0]
            categoria = campos[1]
            estatusDic = 'INVISIBILIZADO'
            logger.info(f'El caso de {nombre} fue invisibilizado')
        elif estatus == 'duda':
            folio = campos[0]
            categoria = campos[1]
            estatusDic = 'DUDA'
            logger.info(f'El caso de {nombre} debe revisarse')
        elif estatus == 'no borrado':
            folio = campos[0]
            categoria = campos[1]
            estatusDic = 'NO BORRADO'
            logger.info(f'El caso de {nombre} no fue borrado')
        else:
            logger.error('Hay un error con el estatus asignado')
        diccionario['Folio'].append(folio)
        diccionario['Categoría'].append(categoria)
        diccionario['Estatus'].append(estatusDic)
    

    if len(campos) == 1:
        encontrarEstatus('borrado', campos, datosDesaparecidos)
    else:
        nombreCampos = f'{campos[2]} {campos[3]} {campos[4]}'
        estadoCampos = campos[10]
        if nombre == nombreCampos:
            if estado == estadoCampos:
                encontrarEstatus('no borrado', campos, datosDesaparecidos)
            elif estadoCampos == 'SE DESCONOCE':
                encontrarEstatus('duda', campos, datosDesaparecidos)
            else:
                encontrarEstatus('borrado', campos, datosDesaparecidos)
        elif 'INFORMACIÓN' in campos[2]:
            if estado == estadoCampos:
                encontrarEstatus('invisibilizado', campos, datosDesaparecidos)
            else:
                encontrarEstatus('borrado', campos, datosDesaparecidos)
        else:
            encontrarEstatus('borrado', campos, datosDesaparecidos)

driver.quit()

df = pd.DataFrame(datosDesaparecidos)

desaparecidosBorradosCompleto = pd.merge(desaparecidosBorrados, df, on='Nombre', how='inner')
desaparecidosBorradosCompleto.to_csv('cedulas/Datos/desaparecidos_borrados.csv', index=False)