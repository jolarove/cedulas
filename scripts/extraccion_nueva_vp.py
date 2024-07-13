"""
Usamos la paquetería Selenium para navegar y extraer los datos de la nueva versión del RNPDNO
Con Pandas generamos la base de datos y la exportamos en formato csv
Con logging gestionamos los mensajes y alertas
"""

#PAQUETERÍAS
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd 
import time 
import logging

#FUNCIONES
def abrirNavegador(website, pathEspera, intentosMaximos, delay):
    """
    Instala el WebDriver de Chrome
    Abre el navegador Chrome y el sitio especificado con ventana maximizada

    Parámetros:
    website (str): web a abrir
    pathEspera (xpath): Elementos que buscaremos en el sitio para gestionar el tiempo de espera
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
            espera = WebDriverWait(driver, 60).until(
                EC.visibility_of_all_elements_located((By.XPATH, pathEspera))
            )
            return driver
        except Exception as e:
            logger.warning(f'Intento {intento + 1} de {intentosMaximos}, fallido: {e}')
            intento += 1
            time.sleep(delay)
    
    raise Exception(f'No se pudo abrir el navegador después de {intentosMaximos} intentos')

def cargaEspera():
    """
    Gestiona el avance de los procesos hasta que termine la carga de la misma web
    """
    elemento = (By.XPATH, '//img[@alt="IMAGEN CNB"]')
    espera = WebDriverWait(driver, 30)
    espera.until(EC.invisibility_of_element_located(elemento))

#ACCIONES

#Configuramos el logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#Definimos los parámetros para la función de abrirNavegador
website = 'https://consultapublicarnpdno.segob.gob.mx/consulta'
pathEspera = '//div[@class="ctn-info-consulta"]//div[@class="row"]//div[@class="col-6 col-md-4 col-lg-4 col-xl-2 margin-col"]'
intentos, delay = 5, 5

#Abrimos el navegador
driver = abrirNavegador(website, pathEspera, intentos, delay)
time.sleep(3)

#Creamos el diccionario para almacenar los datos extraidos
claves = ['Nombre', 'Edad', 'Sexo', 'Estatus', 'Fecha', 'Estado', 'Información reservada']
datosRegistro = {clave: [] for clave in claves}

#Gestiomanos la vista de los registros como lista y no como cédulas
btnLista = driver.find_element(by='xpath', value='//button//span[contains(text(), "Ver Lista")]')
driver.execute_script("arguments[0].click();", btnLista)

#Ubicamos el selector de los estados, iteremos estado por estado
estados = driver.find_elements(by='xpath', value='(//select[@class="form-select form-select-sm"])[1]//option')

#Iteramos por cada estado, omitimos la primera opción, dado que es 'Selecciona un estado' y no nos sirve
for estado in estados[1:]:
    cargaEspera()
    #Encontramos el nombre del estado
    nombreEstado = estado.text
    logger.info(f'Comenzamos extracción de datos de {nombreEstado}')
    #Creamos un diccionario temporal para almacenar los datos por estado
    datosTemporales = {clave: [] for clave in claves}
    #Damos click en el estado
    estado.click()
    #Ubicamos y damos click en el botón buscar
    btnBusqueda = driver.find_element(by='xpath', value='//button[@class="btn-busqueda-consulta"]')
    driver.execute_script("arguments[0].click();", btnBusqueda)
    #Esperamos que cargue
    time.sleep(1)
    cargaEspera()

    #Encontramos la cantidad de registros a extraer por estado    
    txtRegistros = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.XPATH, '//span[@class="m-2"]'))
        ).text
    totalRegistros = int(txtRegistros.split(" ")[0].replace(",",""))
    logger.info(f'La base de datos contiene {totalRegistros} registros')

    #Inicializamos una variable de control que nos servirá para gestionar el ciclo while
    registroActual = 0
    #Corremos un ciclo while que se frenará cuando descarguemos todos los registros del estado
    while registroActual < totalRegistros:
        cargaEspera()
        #Buscamos y encontramos la tabla con los registros
        tabla = driver.find_element(by='xpath', value='//table[@class="table table-responsive"]')
        filas =WebDriverWait(tabla, 10).until(
            EC.visibility_of_all_elements_located((By.XPATH, './/tbody//tr'))
            )
        #Iteramos por cada fila para extraer los datos que contenga
        for fila in filas:
            nombre = fila.find_element(by='xpath', value='.//td[2]').text
            apellido1 = fila.find_element(by='xpath', value='.//td[3]').text
            apellido2 = fila.find_element(by='xpath', value='.//td[4]').text
            #Obtenemos el nombre completo
            nombreCompleto = f'{nombre} {apellido1} {apellido2}'
            edad = fila.find_element(by='xpath', value='.//td[5]').text
            sexo = fila.find_element(by='xpath', value='.//td[6]').text
            estatus = fila.find_element(by='xpath', value='.//td[7]').text
            fecha = fila.find_element(by='xpath', value='.//td[8]').text
            estado = fila.find_element(by='xpath', value='.//td[9]').text
            reservada = fila.find_element(by='xpath', value='.//td[10]').text
            #Actualizamos la variable de control
            registroActual += 1
            logger.info(f'Información de {nombreCompleto} extraida. Van {registroActual} de {totalRegistros}')
            
            #Enviamos los datos extraidos al diccionario temporal
            datosTemporales['Nombre'].append(nombreCompleto)
            datosTemporales['Edad'].append(edad)
            datosTemporales['Sexo'].append(sexo)
            datosTemporales['Estatus'].append(estatus)
            datosTemporales['Fecha'].append(fecha)
            datosTemporales['Estado'].append(estado)
            datosTemporales['Información reservada'].append(reservada)

        #Gestionamos la paginación
        if registroActual < totalRegistros:
            #Encontramos y damos clic en el botón de siguiente página
            paginacion = driver.find_element(by='xpath', value='//nav[@data-pc-section="paginatorwrapper"]')
            btnSiguiente = paginacion.find_element(by='xpath', value='.//button[@aria-label="Next Page"]')
            driver.execute_script("arguments[0].click();", btnSiguiente)
    
    #Enviamos los datos del diccionario temporal, al diccionario final
    for clave in datosTemporales:
        datosRegistro[clave].extend(datosTemporales[clave])
    logging.info(f'Terminó el proceso de {nombreEstado}')
    logging.info(f'Van {len(datosRegistro['Nombre'])} datos extraidos')

    #Regresamos la paginación a la página 1
    btnReinicio = paginacion.find_element(by='xpath', value='.//button[@aria-label="First Page"]')
    driver.execute_script("arguments[0].click();", btnReinicio)

#Cerramos el navegador
driver.quit()

#Creamos la base de datos con el diccionario final
df = pd.DataFrame(datosRegistro)
#La exportamos en formato csv
df.to_csv('Connectas/cedulas/Datos/nueva_Versión_Pública.csv', index=False)
logger.info('Proceso terminado con éxito')