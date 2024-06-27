"""
Usamos la paquetería de selenium con apoyo de time para navegar en el sitio web de la Búsqueda Generalizada de
Desaparecidos del Gobierno de México y obtenermos la base de datos con todos los registros disponibles

El webdriver lo instalamos de forma automática y no manual y utilizamos ChromeDriver

Con pandas generamos el data frame y lo guardamos en formato csv

Con logging manejamos los mensajes informativos, de errores, etcétera
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


def vista100(driver):
    """
    Configura la vista de la tabla para mostrar 100 registros a la vez
    
    Parámetros:
    driver (WebDriver)
    """
    seleccion = driver.find_element(by='xpath', value='//select[@name="t-busq_length"]//option[@value="100"]')
    seleccion.click()
    time.sleep(3)

def siguiente(driver):
    """
    Navega en la siguiente página de la tabla

    Utilizamos la función clic de Python para la paginación, sino funciona, damos clic con js

    Parámetros:
    driver(WebDriver)
    """
    btnSiguiente = driver.find_element(by='xpath', value='//a[@id="t-busq_next"]')
    try:
        btnSiguiente.click()
    except:
        driver.execute_script("arguments[0].click();", btnSiguiente)
    time.sleep(1.5)  

def actualizarPagina(driver, lista, website):
    """
    Actualiza el sitio en caso de errores y navega hasta la página de avance

    Parámetros:
    driver(WebDriver)
    lista(list): lista de elementos extraidos
    website(str): sitio web de navegación

    Retorna:
    tupla: WebDriver actualizado, tabla encontrada y página actual
    """
    logger.warning('Problemas, el sitio se recargará')
    paginaActual = len(lista)/100
    logger.info(f'Reiniciamos en la página {paginaActual}')
    driver.get(website)
    logger.info('El sitio se recargó')
    time.sleep(5) 
    vista100(driver) 
    tabla = driver.find_element(by='id', value='t-busq') 
    paginaActual = int(paginaActual)
    if paginaActual != 1:
        for _ in range(paginaActual):
            siguiente(driver) 
    return driver, tabla, paginaActual

def añadirDatos(diccionarioTemporal, diccionarioFinal):
    """
    Añade los datos de un diccionario temporal a uno final

    Parámetros:
    diccionarioTemporal(dict): diccionario utilizado para almacenar datos extraidos en ciclo for
    diccionarioFinal(dict): diccionario donde se añadirán los nuevos datos tras el ciclo for
    """        
    for clave in diccionarioTemporal:
        diccionarioFinal[clave].extend(diccionarioTemporal[clave])

#ACCIONES

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#Definimos variables para el driver
website = 'https://busquedageneralizada.gob.mx/consulta/'
espera = 5 

#Abrimos el navegador
driver = abrirNavegador(website, espera, 5, 5) 

#Seleccionamos que la tabla muestre cien registros a la vez
vista100(driver)

#Encontramos la cantidad de páginas que tiene la tabla y convertimos el dato en entero
paginacion = driver.find_elements(by='xpath', value='//a[@class="paginate_button "]')
ultimaPaginaTexto = paginacion[-1].text 
ultimaPagina = ultimaPaginaTexto.replace(",", "")
ultimaPagina = int(ultimaPagina)
logger.info(f'La tabla está dividida en {ultimaPagina} páginas')

#Definimos en cuál página de la tabla estamos
paginaActual = 1

#Definimos las claves para el diccionario, serán las columnas del data frame final
claves = ['Folio', 'Categoría', 'Nombre completo', 'Edad', 'Sexo', 'Nacionalidad', 
        'Fecha desaparición', 'Autoridad', 'Estado']

#Con bucle for enviamos las claves a un diccionario y como valores colocamos listas vacías
desaparecidosDatos = {clave: [] for clave in claves}

#Con un ciclo while navegaremos en todas las páginas de la tabla
while paginaActual <= ultimaPagina:
    try:
        tabla = driver.find_element(by='id', value='t-busq') #buscamos la tabla
    except:
        #Si no encuentra la tabla, actualizamos el sitio web y volvemos a buscar la tabla
        driver, tabla, paginaActual = actualizarPagina(driver, desaparecidosDatos['Folio'], website)
        

    #Una vez que detecta la tabla, encontramos las filas, cada fila es un registro       
    desaparecidos = tabla.find_elements(by='xpath', value='.//tbody//tr') 

    """
    Creamos un diccionario temporal exactamente igual que el final, pero para almacenar los datos de cada for
    y luego inicializarse vacío. Es necesario porque se detectó que el sitio web puede fallar antes de que
    termine la extracción de la pagina completa de la tabla, por lo tanto, generaba un error al momento 
    de actualizar y buscar el avance que se tenía.
    Con esto, si se extraen los cien registros se avanza, sino, se actualiza y se intentan extraer, de nuevo,
    los cien registros.
    """
    desaparecidosDatosTemp = {clave: [] for clave in claves}

    #Bucle for para extraer los datos de cada fila de la tabla
    for desaparecido in desaparecidos:
        try:
            folio = desaparecido.find_element(by='xpath', value='.//td[1]').text
            categoria = desaparecido.find_element(by='xpath', value='.//td[2]').text
            nombre = desaparecido.find_element(by='xpath', value='.//td[3]').text
            primerApellido = desaparecido.find_element(by='xpath', value='.//td[4]').text
            segundoApellido = desaparecido.find_element(by='xpath', value='.//td[5]').text
            edad = desaparecido.find_element(by='xpath', value='.//td[6]').text
            sexo = desaparecido.find_element(by='xpath', value='.//td[7]').text
            nacionalidad = desaparecido.find_element(by='xpath', value='.//td[8]').text
            fecha = desaparecido.find_element(by='xpath', value='.//td[9]').text
            autoridad = desaparecido.find_element(by='xpath', value='.//td[10]').text
            estado = desaparecido.find_element(by='xpath', value='.//td[11]').text
            logger.info(f'Desaparecido: {nombre} {primerApellido} {segundoApellido}')

            #Enviamos la información al diccionario temportal
            desaparecidosDatosTemp['Folio'].append(folio)
            desaparecidosDatosTemp['Categoría'].append(categoria)
            #Concatenamos para tener el nombre completo en vez de dividido
            desaparecidosDatosTemp['Nombre completo'].append(f'{nombre} {primerApellido} {segundoApellido}')
            desaparecidosDatosTemp['Edad'].append(edad)
            desaparecidosDatosTemp['Sexo'].append(sexo)
            desaparecidosDatosTemp['Nacionalidad'].append(nacionalidad)
            desaparecidosDatosTemp['Fecha desaparición'].append(fecha)
            desaparecidosDatosTemp['Autoridad'].append(autoridad)
            desaparecidosDatosTemp['Estado'].append(estado)
        except Exception as e:
            logger.error("Error en la extracción: {e}")
            pass 
            
    """
    Con una condicionante revisamos si el diccionario temporal tiene cien registros, si sí, los enviamos
    al diccionario final. Si no, se finaliza la iteración while y al inicio de la siguiente se actualiza
    el sitio web
    """
    if len(desaparecidosDatosTemp['Folio']) == 100:
        añadirDatos(desaparecidosDatosTemp, desaparecidosDatos)
        logger.info('Todo correcto con la extracción de esta página')
        logger.info(f"Van {len(desaparecidosDatos['Nombre completo'])} registros extraidos con éxito")
        #Usamos esta condicionante para dar clic o no en el botón siguiente       
        if paginaActual < ultimaPagina:
            siguiente(driver)
                
        #Actualizamos el valor de la página actual 
        paginaActual += 1 
    elif paginaActual == ultimaPagina:
        """
        La última página de la tabla no tiene cien registros exactos, por lo tanto, si estamos en ella
        indicamos que envíe los datos del diccionario temporal al final sin importan cuántos sean, 
        así evitamos que el bucle while sea infinito
        """
        añadirDatos(desaparecidosDatosTemp, desaparecidosDatos)
        
        logger.info('Todo correcto, finalizamos extracción')
        logger.info(f"Extragimos con éxito un total de {len(desaparecidosDatos['Nombre completo'])} registros")
        #Actualizamos la página actual, con esto, página actual será mayor que última página y se rompe el ciclo while
        paginaActual += 1 
    else: 
        logger.error('Error, la página se actualizará. Espera, por favor')

    
#Cerramos el navegador
driver.quit() 

#Creamos el data frame
df = pd.DataFrame(desaparecidosDatos)

#Guardamos el df en formato csv
df.to_csv('cedulas/version_publica_dic2023.csv', index=False)


