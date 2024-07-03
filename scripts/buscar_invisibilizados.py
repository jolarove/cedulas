"""
Usamos Selenium y time para navegar en la plataforma de la versión pública de diciembre del RNPD con el fin 
de verificar registro por registro de los casos borrados y cédulas sin registro, para encontrar los
casos invisibilizados, es decir, aquellos que sí están en el RNPD, pero con datos confidenciales
o reservados.

Con Pandas leemos, analizamos y generamos los data frames.

Con logging gestionamos los mensajes.
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

def encontrarEstatus(estatus, campos, diccionario, nombre):
    """
    Define el estatus entre: borrado, invisibilizado, dudoso o no borrado y lo envía a un diccionario.

    Parámetros:
    estatus(str): estatus a asignar
    campos(list): lista con los campos encontrados en la tabla de registros del RNPD
    diccionario(dict): diccionario al cual se enviarán los datos sobre el estatus definido
    nombre(str): nombre de la persona desaparecida a asignar estatus
    """
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
    """
    Filtra un data frame

    Parámetros:
    df(df): data frame que se pretende filtrar
    estatus(str): valor que se usará para el filtro

    Retorna:
    dfFiltrado: nuevo data frame con los valores filtrados
    """
    filtro = df['Estatus'] == estatus
    dfFiltrado = df[filtro]
    return dfFiltrado

def extraccionDatos(campos, diccionario, nombre, estado):
    """
    Extrae los datos de la plataforma del RNPD

    Parámetros:
    campos(list): lista con los campos encontrados en la tabla del registro de desaparecidos
    diccionario(dict): diccionario a donde se enviará la información extraida
    nombre(str): nombre de la persona desaparecida
    estado(str): estado donde desapareció la persona
    """
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
    """
    Navega en el sitio para confirmar el estatus de la persona desaparecida entre: borrado, no borrado,
    con duda e invisibilizado

    Parámetros:
    df(df): data frame donde están los datos a confirmar
    drive(WebDriver): navegador con el sitio web de la plataforma del RNPD listo para iterar

    Retorna:
    diccionario(dict): diccionario con los datos extraidos y el estatus asignado
    """
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

#Definimos los valores para abrir el sitio web
website = 'https://busquedageneralizada.gob.mx/consulta/'
espera = 5

#Importamos la base de datos de los desaparecidos con cédula activa que fueron borrados del RNPD
cedulasBorradas = pd.read_csv('cedulas/Datos/cedulas_borradas.csv')

#Abrimos el navegador
driver = abrirNavegador(website, espera, 5, 5)

#Extraemos los datos y asignamos el estatus, todo lo enviamos a un diccionario
datosDesaparecidos = confirmarEstatus(cedulasBorradas, driver)

#Cerramos el navegador
driver.quit()

#Creamos un nuevo data frame con el diccionario creado anteriormente
df = pd.DataFrame(datosDesaparecidos)

#Unimos los dos data frames para obtener uno con todos los datos que necesitamos
desaparecidosBorrados = pd.merge(cedulasBorradas, df, on='Nombre', how='inner')

#Filtramos para encontrar sólo las cédulas que confirmamos fueron borradas del RNPD
desaparecidosBorradosCompleto = filtroEstatus(desaparecidosBorrados, 'BORRADO')

#Filtramos para encontrar sólo los casos invisibilizados
dfInvidibilizados = filtroEstatus(desaparecidosBorrados, 'INVISIBILIZADO')

#Exportamos en formato csv el data frame con los casos borrados
desaparecidosBorradosCompleto.to_csv('cedulas/Datos/desaparecidos_borrados.csv', index=False)
logger.info(f'El gobierno de México borró {len(desaparecidosBorradosCompleto)} casos del RNPD')

#Importamos el data frame con las cédulas que no están en el RNPD
cedulasSinRegistro = pd.read_csv('cedulas/Datos/cedulas_sin_registro.csv')

#Abrimos el navegador de nuevo
driver = abrirNavegador(website, espera, 5, 5)

#Extraemos datos del RNPD, asignamos el estatus a cada cédula no integradas y enviamos a diccionario
datosCedulas = confirmarEstatus(cedulasSinRegistro, driver)

#Cerramos el navegado
driver.quit()

#Creamos un data frame con los datos del diccionario
df = pd.DataFrame(datosCedulas)

#Unimos los dos data frames
dfCedulas = pd.merge(cedulasSinRegistro, df, on='Nombre', how='inner')

#Filtamos para encontrar los casos invisibilizados
dfCedulasInvisibilizados = filtroEstatus(dfCedulas, 'INVISIBILIZADO')
#Concatenamos los dos data frames de casos invisibilizados
dfInvisibilizadosFinal = pd.concat([dfInvidibilizados, dfCedulasInvisibilizados], ignore_index=True)
#Exportamos el nuevo data frame en formato csv
dfInvisibilizadosFinal.to_csv('cedulas/Datos/desaparecidos_invisibilizados.csv', index=False)
logger.info(f'El gobierno de México invisibilizó a {len(dfInvisibilizadosFinal)} casos de desaparecidos')

#Filtramos por si hubiera casos que, al hacer la verificación, se confirmara que siempre estuvieron en el RNPD
#Al final, esta data frame debería estar vacío, si no es así, hay que verificar el proceso de limpieza y análisis
dfIncluidas = filtroEstatus(dfCedulas, 'NO BORRADO')
dfIncluidas.to_csv('cedulas/Datos/incluidas_revision.csv', index=False)
if len(dfIncluidas) == 0:
    logger.info('Análisis finalizado con éxito')
else:
    logger.warning('ADVERTENCIA: revisar el proceso de limpieza y análisis, algo salió mal')
