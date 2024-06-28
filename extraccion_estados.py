"""
Usamos la paquetería Selenium junto con time para navegar por las páginas de las comisiones de búsqueda de 
Jalisco, Estado de México, Guanajuato, Puebla, Tabasco y Veracruz para extraer los datos de personas
desaparecidas de las cuales hay cédula de búsqueda oficial.

Utilizamos Pandas para generar las bases de datos extraidas y exportarlas en formato csv

Con logging gestionamos los mensajes de información, alertas, errores, etc.

Con json accedemos al archivo donde tenemos los enlaces de los estados para la extracción de datos.

Con urllib gestionamos las urls para obtener datos en el caso del Estado de México

Con re gestionamos las expresiones regulares
"""
#PAQUETERÍAS
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium import webdriver 
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd 
import time 
import logging
import json
from urllib.parse import unquote
import re

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
    opciones.add_argument('--headless')
    opciones.add_argument('--start-maximized')
    intento = 0
    while intento < intentosMaximos:
        try:
            servicio = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=servicio, options=opciones)
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

def diccionarios(claves):
    """
    Crea los diccionarios para almacenar los datos extraidos de los sitios web

    Parámetros: 
    claves(list): lista con las claves que, al final se convertirán en las columnas de la base de datos.

    Retorna:
    diccionario(dict): diccionario con claves, pero vacío para almacenar datos.
    """
    diccionario = {clave: [] for clave in claves}
    return diccionario

def crearDf(datos, estado):
    """
    Crea un data frame y lo exporta en formato csv

    Parámetros:
    datos(dict): diccionario donde están almacenados los datos extraidos
    estado(str): nombre del estado al que pertenecen esos datos
    """
    df = pd.DataFrame(datos)
    df.to_csv(f'cedulas/{estado}/datos_cedulas_{estado}.csv', index=False)

def scroll_al_final(driver):
    """
    Hace scroll hasta el final de la página

    Parámetros:
    driver(WebDriver)
    """
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5) 

def cerrar(btn):
    """
    Cierra cuadro de diálogo

    Parámetros:
    btn(button): botón que cierra el cuadro de diálogo
    """
    btnCerrar = driver.find_element(by='xpath', value=btn)
    btnCerrar.click()
    time.sleep(2)
    
#ACCIONES

#Configuramos el logger para los mensajes
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#Importamos los datos de los enlaces para la extracción
with open('cedulas/enlaces_estados.json', 'r',  encoding='utf-8') as archivo_json:
    websites = json.load(archivo_json)
espera = 5 

"""
No nos es funcional un bucle porque cada sitio web tiene estructura distinta, estonces tendrán que 
ser procesos individualizados por cada estado.
"""
######ESTADO DE MEXICO######
"""
El primer estado del que extraeremos sus datos sobre las cédulas de búsqueda es el Estado de México.
Particularidades: el sitio tiene carga infinita, pero la extracción es muy rápida, pues no tiene paginación,
el sitio tiene una complejidad que no detecta el texto en la etiqueta p donde está el nombre, por lo tanto
lo extraemos desde la url de la imagen.
"""
#Abrimos el navegador
driver = abrirNavegador(websites['Estado de México'], espera, 5, 5, True) 

#Creamos el diccionario para almacenar datos
claves = ['Nombre', 'Mes', 'Año', 'Url']
datosEdoMex = diccionarios(claves)

#Encontramos las imágenes
imagenesDesaparecidos = driver.find_elements(by='xpath', value='//div[@class="accordion-body"]//img')
  
#Con un bucle for extraemos los datos de cada url encontrada
for imagen in imagenesDesaparecidos:
    try:
        url = imagen.get_attribute('src')
    except Exception as e:
        logger.warning('La url no existe o no se pudo extraer')
        url = 'Sin imagen'
    try:
        #Descomponemos la URL para obtener los datos
        nombreUrl = url.split("/")[-1] #Elegimos la parte final de la URL donde está el nombre
        nombreExtension = nombreUrl.split(".")[0] #Eliminamos la extensión después del punto
        nombreFinal = unquote(nombreExtension) #Convertimos los caracteres especiales, por ejemplo espacios
    except Exception as e:
        logger.error('No se pudo encontrar el nombre')
        nombreFinal = 'Error'
    logger.info(f'Nombre desaparecido: {nombreFinal}')
    mes = url.split("/")[-2] #Obtenemos el mes de la URL
    anio = url.split("/")[-3] #Obtenemos el año de la URL
    
    #Enviamos los datos al diccionario
    datosEdoMex['Nombre'].append(nombreFinal)
    datosEdoMex['Mes'].append(mes)
    datosEdoMex['Año'].append(anio)
    datosEdoMex['Url'].append(url)

#Cerramos el navegador
driver.quit()
#Creamos y guardamos el df
crearDf(datosEdoMex, 'Estado de México')
logger.info('Base de datos creada y exportada con éxito')

######GUANAJUATO#######
"""
El siguiente estado es Guanajuato.
Particularidades: Es necesario hacer scroll hasta el final de la página y esperar a que cargue
el último elemento para poder extraer correctamente los datos. 
Tiene tres secciones: Alerta Ámber, Protocolo Alba y generales.
"""
#Abrimos el navegador
driver = abrirNavegador(websites['Guanajuato'], espera, 5, 5, False)

#Creamos el diccionario
claves = ['Nombre', 'Fecha', 'Tipo' 'Url']
datosGuanajuato = diccionarios(claves)

#Damos scroll hasta el final de la página y esperamos a que el último elemento esté cargado
scroll_al_final(driver)
ultimoElemento = WebDriverWait(driver, 15).until(
     lambda d: d.find_element(by='xpath', value='(//h5[@class="card-title"])[last()]').text.strip() != "")

#Encontramos las cédulas
alertasAmber = driver.find_elements(by='xpath', value='//div[@id="listadoAmbar"]//div[@data-aos="fade-up"]')
albas = driver.find_elements(by='xpath', value='//div[@id="listadoAlba"]//div[@data-aos="fade-up"]')
generales = driver.find_elements(by='xpath', value='//div[@id="listado"]//div[@data-aos="fade-up"]')
cedulas = [alertasAmber, albas, generales]

for grupo in cedulas:
    for cedula in grupo:
        nombre = cedula.find_element(by="xpath", value='.//h5').text
        urlImg = cedula.find_element(by="xpath", value='.//img').get_attribute('src')

        datosGuanajuato['Nombre'].append(nombre)
        datosGuanajuato['Url'].append(nombre)
datosGuanajuato['Fecha'].extend(["Sin dato"]*len(alertasAmber))
datosGuanajuato['Fecha'].extend(["Sin dato"]*len(albas))

#Iteramos para extraer las fechas de las cédulas generales que sí cuentan con el dato
for cedula in generales:
    #Es necesario encontrar un botón y presionarlo para extraer
    boton = cedula.find_element(by='xpath', value='.//button') 
    driver.execute_script("arguments[0].click();", boton)
    #Usamos una combinación de esperas para extraer los datos
    fechaTexto = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, 
                                                                                   './/div[@class="date"]//p')))
    time.sleep(1)
    #Borramos espacios
    fecha = fechaTexto.text.strip()
    try:
        #Si tiene disponible el dato de fecha, lo extraemos
        datosGuanajuato['Fecha'].append(fecha.split()[1]) 
    except Exception as e:
        logger.info('No hay fecha disponible')
        #Sino, colocamos que no hay dato
        if fecha == "FECHA":
            datosGuanajuato['Fecha'].append("Sin dato")
        else:
            datosGuanajuato['Fecha'].append(fecha)

#Cerramos el navegador   
driver.quit()

#Creamos y exportamos la base de datos
crearDf(datosGuanajuato, 'Guanajuato')

####JALISCO####
"""
Jalisco es la siguiente entidad federativa.
Particularidades: En este estado tienen un sitio web mejor estructurado. La descarga es más lenta 
ya que son más registros y tiene paginación, pero hay más información disponible.
"""
#Abrimos el navegador
driver = abrirNavegador(websites['Jalisco'], espera, 5, 5, False)

#Creamos el diccionario
claves = ['Nombre', 'Estatus', 'Edad', 'Sexo', 'Género', 'Fecha', 'Lugar', 'Url']
datosJalisco = diccionarios(claves)

#Damos clic en el botón buscar para que muestre todas las cédulas y esperamos que cargue
buscar = driver.find_element(by="xpath", 
                             value="//button[@class='MuiButtonBase-root MuiIconButton-root MuiIconButton-sizeMedium css-18mwzm8']")
buscar.click()
time.sleep(10) 

#buscamos el panel de paginación y definimos el límite para el ciclo
paginacion = driver.find_element(by='xpath', value='//ul[@class="MuiPagination-ul css-nhb8h9"]')
paginas = paginacion.find_elements(by='tag name', value='li')
ultimaPagina = int(paginas[-2].text)
paginaActual = 1

#comenzamos la navegación y descargamos todo lo descargable
while paginaActual <= ultimaPagina:
    cajaCedulas = driver.find_element(by='xpath', value='//div[1]/div[1]/div[2]/div/div[2]/div[2]')
    cedulas = cajaCedulas.find_elements(by='xpath', value='.//div[@class="MuiBox-root css-13pkf70"]')
    for cedula in cedulas:
        nombre = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-apx2uo")]//p[contains(@class, "css-445tfr")])[1]').text
        estatus = cedula.find_element(by='xpath', value='.//p[contains(@class, "css-k2vnwu")]').text
        edad = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-apx2uo")]//p[contains(@class, "css-445tfr")])[2]').text
        sexo = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[1]//td[2]//p)[1]').text
        genero = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[1]//td[4]//p)[1]').text
        fecha = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[1]//td[2]//p)[2]').text
        lugar = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[2]//td[2]//p)[2]').text
        try:
            img = cedula.find_element(by='xpath', value='.//img[@alt="Imagen"]').get_attribute('src')
        except Exception as e:
            logger.error(f'No hay imagen disponible: {e}')
            img = 'Sin datos'
        logger.info(f'Desaparecido: {nombre}')

        #Enviamos la información al diccionario
        datosJalisco['Nombre'].append(nombre)
        datosJalisco['Estatus'].append(estatus)
        datosJalisco['Edad'].append(edad)
        datosJalisco['Sexo'].append(sexo)
        datosJalisco['Género'].append(genero)
        datosJalisco['Fecha'].append(fecha)
        datosJalisco['Url'].append(img)

    #Damos clic en el botón siguiente página, siempre y cuando no estemos en la última
    if paginaActual < ultimaPagina:
        botonSiguiente = driver.find_element(by='xpath', value='//li//button[@aria-label="Go to next page"]')
        botonSiguiente.click()
    paginaActual += 1
    time.sleep(1)

#Cerramos el navegador web
driver.quit()

#Creamos el df y lo exportamos
crearDf(datosJalisco, 'Jalisco')

#####PUEBLA######
"""
El siguiente estado es Puebla
Particularidades: No distingue entre localizados y desaparecidos. La ventaja es que duplica cédulas,
es decir, cuando localizan a una persona publican la cédula de localizado sin eliminar la de desaparecido,
por lo tanto, si encontramos los duplicados podremos filtrar entre desaparecidos y localizados, esto 
se hará en el algoritmo de análisis, aquí sólo se descarga. Hay paginación.
"""
#Abrimos el sitio
driver = abrirNavegador(websites['Puebla'], espera, 5, 5, False)

#Encontramos el total de páginas que tiene el contenedor de las cédulas y lo convertimos a entero
contadorPaginas = driver.find_element(by='xpath', value='//div[@class="k2PaginationCounter"]').text
ultimaPagina = contadorPaginas.split(" ")[-1]
ultimaPagina = int(ultimaPagina)
logger.info(f'En total hay {ultimaPagina} páginas')

#Definimos la variable de la página actual
paginaActual = 1

#Creamos un diccionario con las claves según los datos disponibles para extraer
claves = ['Nombre', 'Url']
datosPuebla = {clave: [] for clave in claves}

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
        datosPuebla['Nombre'].append(nombre)
        datosPuebla['Url'].append(urlImagen)
        logger.info(f'Registro de {nombre}')
    
    #Con una condicionante damos clic en el botón siguiente, si se está en la última página, no se dará clic
    if paginaActual < ultimaPagina:
        btnSiguiente = driver.find_element(by='xpath', value='//a[@aria-label="Ir a la página siguiente"]')
        driver.execute_script("arguments[0].click();", btnSiguiente)
    #Se actualiza la variable de la página actual
    paginaActual += 1

#Cerramos el navegador
driver.quit()

#Creamos la base de datos y la exportamos
crearDf(datosPuebla, 'Puebla')

#####Tabasco######
"""
Sigue Tabasco
Particularidades: no funciona con el proceso visible, hay que ocultarlo. No es necesaria la paginación
"""
driver = abrirNavegador(websites['Tabasco'], espera, 5, 5, False)
#Buscamos el selector y le especificamos que nos muestre todos los registros en la tabla,
#así evitamos la paginación
selector = driver.find_element(by='xpath', value='//select[@name="dataTable_length"]')
todos = selector.find_element(by='xpath', value='.//option[@value="-1"]')
todos.click()
time.sleep(3)

#Buscamos la tabla y los registros
tabla = driver.find_element(by='id', value='dataTable')
registros = tabla.find_elements(by='xpath', value='.//tbody//tr')

#Creamos el diccionario
claves = ['Nombre', 'Sexo', 'Estatus', 'Url']
datosTabasco = diccionarios(claves)

#Con un bucle for iteramos entre las filas y columnas para extraer la información y enviarla a las listas
for registro in registros:
    nombre = registro.find_element(by='xpath', value='.//td[1]')
    sexo = registro.find_element(by='xpath', value='.//td[2]')
    estado = registro.find_element(by='xpath', value='.//td[3]')
    url = registro.find_element(by='xpath', value='.//td[4]')

    #Eviamos al diccionario
    datosTabasco['Nombre'].append(nombre.text)
    logger.info(nombre.text)
    datosTabasco['Sexo'].append(sexo.text)
    datosTabasco['Estatus'].append(estado.text)
    link = url.find_element(by='tag name', value='a').get_attribute('href')
    datosTabasco['Url'].append(link)

driver.quit() #Cerramos el navegador

#Creamos y exportamos la base de datos
crearDf(datosTabasco, 'Tabasco')

####VERACRUZ#####
"""
Veracruz es el último estado
Particularidades: Tiene debidamente identificados a desaparecidos y localizdos. Hay paginación.
"""
#Abrimos el navegador
driver = abrirNavegador(websites['Veracruz'], espera, 5, 5, False)

#Al inicio aparece un cuadro de diálogo que hay que cerrar
btn = '//button[@class="btn btn-outline-secondary"]' #Detectamos el botón y cerramos el cuadro de diálogo
cerrar(btn)

#Definimos el diccionario
claves = ['Nombre', 'Fecha', 'Estatus', 'Url']
datosVeracruz = diccionarios(claves)

#Buscamos el selector y obtenemos las opciones disponibles para extraer los datos
estatusSelector = driver.find_elements(by='xpath', value='//select[@id="idArea"]//option')

#Con un ciclo for damos clic en cada opción y extraemos los datos
for estatus in estatusSelector:
    estatus.click()
    estado = estatus.text
    logger.info(f'Descargaremos los registros de {estado}')
    time.sleep(1)
    #Buscamos el botón buscar y damos clic
    btnBuscar = driver.find_element(by='xpath', value='//button[@onclick="buscar1()"]')
    btnBuscar.click()
    time.sleep(3)

    #Buscamos el contenedor donde están los datos
    contenedor = driver.find_element(by='xpath', value='//div[@id="contenedor"]')
    
    #Encontramos el total de elementos en la tabla, lo usaremos para la paginación.
    textoDetalles = contenedor.find_element(by='xpath', value='.//div[@class="details"]//span').text
    #Usamos una expresión relativa para detectar total de casos
    totalCasos = re.search(r'de (\d+) registros', textoDetalles)
    #Lo convertimos a entero, porque lo extrae en cadena de texto
    if totalCasos:
        totalCasos = int(totalCasos.group(1))
        logger.info(f'Extraeremos {totalCasos} casos')
    else:
        logger.error('Hubo un error en obtener el total de casos')
        break
    #Definimos una variable para control y saber cuándo romper el ciclo while
    elementosCapturados = 0

    #Con un ciclo while recorremos las páginas disponibles de la tabla donde están los datos
    while elementosCapturados < totalCasos:
        tabla = driver.find_element(by='id', value='tblResult') #Buscamos la tabla
        #Encontramos la información de las filas de la tabla
        casos = tabla.find_elements(by='xpath', value='.//tbody//tr') 

        #Encontramos la información de cada celda y la agrupamos de acuerdo a las columnas
        for caso in casos:
            nombre = caso.find_element(by='xpath', value='.//td[1]').text
            fecha = caso.find_element(by='xpath', value='.//td[2]').text
            imagen = caso.find_element(by='xpath', value='.//td[3]')

            datosVeracruz['Nombre'].append(nombre)
            if estado == 'No localizadas':
                datosVeracruz['Estatus'].append('Desaparecido')
            else:
                datosVeracruz['Estatus'].append('Localizado')
            elementosCapturados += 1 #Aumentamos en uno la variable de control para el ciclo while
            logger.info(f'Desaparecido: {nombre} y van {elementosCapturados} registros')
            datosVeracruz['Fecha'].append(fecha)
            try:
                url = imagen.find_element(by='xpath', value='.//a').get_attribute('href')
            except Exception as e:
                url = 'Sin imagen'
            datosVeracruz['Url'].append(url)

        #Encontramos la paginación y damos clic
        if elementosCapturados < totalCasos:
            btnSiguiente = driver.find_element(by='xpath', value='//div[contains(text(), "Sig")]')
            try:
                btnSiguiente.click()
            except:
                driver.execute_script("arguments[0].click();", btnSiguiente)
            time.sleep(1)
        
driver.quit() #Cerramos el navegador

#Creamos y exportamos el df
crearDf(datosVeracruz, 'Veracruz')

logger.info('Extracción completada con éxito')