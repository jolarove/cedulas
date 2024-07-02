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

def encontrarEstatus(estatus, campos, diccionario, nombre):
    if estatus == 'borrado':
        folio = 'SIN DATO'
        categoria = 'SIN DATO'
        estatusDic = 'BORRADO'
        nota = ''
        logger.info(f'El caso de {nombre} fue borrado')
    elif estatus == 'invisibilizado':
        folio = campos[0]
        categoria = campos[1]
        estatusDic = 'INVISIBILIZADO'
        nota = campos[2]
        logger.info(f'El caso de {nombre} fue invisibilizado')
    elif estatus == 'duda':
        folio = campos[0]
        categoria = campos[1]
        estatusDic = 'DUDA'
        nota = ''
        logger.info(f'El caso de {nombre} debe revisarse')
    elif estatus == 'no borrado':
        folio = campos[0]
        categoria = campos[1]
        estatusDic = 'NO BORRADO'
        nota = ''
        logger.info(f'El caso de {nombre} no fue borrado')
    else:
        logger.error('Hay un error con el estatus asignado')
    diccionario['Folio'].append(folio)
    diccionario['Categoría'].append(categoria)
    diccionario['Estatus'].append(estatusDic)
    diccionario['Nota'].append(nota)

def filtroEstatus(df, estatus):
    filtro = df['Estatus'] == estatus
    dfFiltrado = df[filtro]
    return dfFiltrado

def extraccionDatos(campos, diccionario, nombre, estado):
            if len(campos) == 1:
                encontrarEstatus('borrado', campos, diccionario, nombre)
            else:
                nombreCampos = f'{campos[2]} {campos[3]} {campos[4]}'
                estadoCampos = campos[10]
                if nombre == nombreCampos:
                    if estado == estadoCampos:
                        encontrarEstatus('no borrado', campos, diccionario, nombre)
                    elif estadoCampos == 'SE DESCONOCE':
                        encontrarEstatus('duda', campos, diccionario, nombre)
                    else:
                        encontrarEstatus('borrado', campos, diccionario, nombre)
                elif 'INFORMACIÓN' in campos[2]:
                    if estado == estadoCampos:
                        encontrarEstatus('invisibilizado', campos, diccionario, nombre)
                    else:
                        encontrarEstatus('borrado', campos, diccionario, nombre)
                else:
                    encontrarEstatus('borrado', campos, diccionario, nombre)

def confirmarEstatus(df, driver):
    claves = ['Nombre','Folio', 'Categoría', 'Estatus', 'Nota']
    diccionario = {clave: [] for clave in claves}
    for i, elemento in df.iterrows():
        inputBusqueda = driver.find_element(by='xpath', value='//input[@type="search"]')
        inputBusqueda.clear()
        nombre = str(elemento["Nombre"])
        estado = str(elemento['Estado'])
        diccionario['Nombre'].append(nombre)
        logger.info(f'Rastreando caso de: {nombre}')
        inputBusqueda.send_keys(nombre)
        time.sleep(1)
        try:
            tabla = driver.find_element(by='tag name', value='table')
        except Exception as e:
            logger.error('Error al extraer, el sitio se actualizará')
            driver.get(website)
            time.sleep(5)
            inputBusqueda = driver.find_element(by='xpath', value='//input[@type="search"]')
            inputBusqueda.send_keys(nombre)
            tabla = driver.find_element(by='tag name', value='table')

        filas = tabla.find_elements(by='xpath', value='.//tbody//tr')
        
        try:
            datos = filas[0].find_elements(by='tag name', value='td')
            campos = [dato.text for dato in datos]
        except:    
            logger.error('Hubo un error al encontrar los datos')
            campos =['SIN DATO']

        extraccionDatos(campos, diccionario, nombre, estado)
    return diccionario

#Configuramos el logger para los mensajes
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

website = 'https://busquedageneralizada.gob.mx/consulta/'
espera = 5

cedulasBorradas = pd.read_csv('cedulas/Datos/cedulas_borradas.csv')

driver = abrirNavegador(website, espera, 5, 5)

datosDesaparecidos = confirmarEstatus(cedulasBorradas, driver)

driver.quit()

df = pd.DataFrame(datosDesaparecidos)

desaparecidosBorrados = pd.merge(cedulasBorradas, df, on='Nombre', how='inner')

desaparecidosBorradosCompleto = filtroEstatus(desaparecidosBorrados, 'BORRADO')
dfInvidibilizados = filtroEstatus(desaparecidosBorrados, 'INVISIBILIZADO')

desaparecidosBorradosCompleto.to_csv('cedulas/Datos/desaparecidos_borrados.csv', index=False)

logger.info(f'El gobierno de México borró {len(desaparecidosBorradosCompleto)} casos del RNPD')

cedulasSinRegistro = pd.read_csv('cedulas/Datos/cedulas_sin_registro.csv')
driver = abrirNavegador(website, espera, 5, 5)

datosCedulas = confirmarEstatus(cedulasSinRegistro, driver)
driver.quit()

df = pd.DataFrame(datosCedulas)

dfCedulas = pd.merge(cedulasSinRegistro, df, on='Nombre', how='inner')
dfCedulasInvisibilizados = filtroEstatus(dfCedulas, 'INVISIBILIZADO')
dfInvisibilizadosFinal = pd.concat([dfInvidibilizados, dfCedulasInvisibilizados], ignore_index=True)
dfInvisibilizadosFinal.to_csv('cedulas/Datos/desaparecidos_invisibilizados.csv', index=False)

dfIncluidas = filtroEstatus(dfCedulas, 'NO BORRADO')
dfIncluidas.to_csv('cedulas/Datos/incluidas_revision.csv', index=False)
logger.info(f'El gobierno de México invisibilizó a {len(dfInvisibilizadosFinal)} casos de desaparecidos')
logger.info('Análisis finalizado con éxito')
