#PAQUETERÍAS
#Para instalar y configurar el driver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.options import Options
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time 
import requests 
import pandas as pd 
import re 
import pyautogui #Para controlar el teclado
#Para descargar las imágenes
from PIL import Image
from io import BytesIO

#FUNCIONES
def cerrar(driver):
    """
    Cerramos el cuadro de diálogo de inicio de sesión en la página para extraer los link de las cédulas

    Parámetros:
    driver(WebDriver)
    """
    cerrar = driver.find_element(by='xpath', value='//div[@aria-label="Cerrar"]')
    cerrar.click()

def scroll(driver):
    """
    Damos scroll a la página donde están los links de las cédulas
    
    Parámetros:
    driver(WebDriver)
    """
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")            
    time.sleep(1) 

def obtenerElementos(driver): 
    """
    Extraemos los elementos necesarios

    Parámetros:
    driver(WebDriver)

    Retorno:
    lista_elementos(list): lista que contiene los elementos extraidos
    """
    try:
        caja_descripcion = driver.find_element(by='xpath', value='//div[@class="xyinxu5 x4uap5 x1g2khh7 xkhd6sd"]') #Extraemos el copy de la publicación si lo hay
        descripcion = caja_descripcion.text
    except:
        descripcion = 'Sin información'
    print(descripcion)
    
    img =WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, '//img[@data-visualcompletion="media-vc-image"]'))
        ) #Encontramos la imagen, usamos espera explícita para que siga hasta que encuentre la Url
    imgUrl = img.get_attribute('src')


    lista_elementos = [descripcion, imgUrl]
    return lista_elementos

def abrirDf(nombre, link, columnas):
    """
    Abrimos o creamos el data frame para almacenar la información

    Parámetros:
    nombre(str): nombre del data frame
    link(url): ruta donde está el data frame
    columnas(list): lista con las columna que debe tener el data frame

    Retorna:
    nombre(df): data frame importado o creado
    """
    #Verificamos si ya existe el csv
    try:
        nombre = pd.read_csv(link)
    except FileNotFoundError: 
        #sino, lo creamos
        nombre = pd.DataFrame(columns=columnas)
        nombre.to_csv(link, index=False)
    return nombre

def extraerEnlaces(lista, index):
    """
    Extraemos todos los enlaces de las publicaciones individuales de cédulas de búsqueda

    Parámetros:
    lista(lista): lista donde se almacenarán los enlaces
    index(i): contador

    """
    #Con un ciclo while iteramos para extraer los enlaces
    while True:
        try:
            #Generamos una lista con todos los enlaces visibles
            linksPublicaciones = driver.find_elements(by='xpath', value='(//div[@class="x1e56ztr"])[1]//a') #Encontramos todas las minitauras de las cédulas
            print(len(linksPublicaciones))

            #Con un if controlamos el proceso para extraer todos los enlaces o hacer scroll
            if index < len(linksPublicaciones):
                #Extraemos el enlace
                linkPublicacion = linksPublicaciones[index].get_attribute('href') #extramos el link de la publicación individual de la cédula
                print(linkPublicacion)
                #Si el enlace tiene estructura web en vez de www, lo modificamos para estandarizar
                if 'web' in linkPublicacion:
                    #Para la modificación del enlace usamos una expresión regular
                    linkPublicacion = re.sub(r'(?<=://)web(?=\.)', 'www', linkPublicacion)

                #Si ese link es el mismo de la primera posición de la base de datos, se corta el bucle, pues ya se actualizó     
                if ultimaImagen == linkPublicacion: 
                    break            

                #Si el link no es el mismo, lo enviamos a la lista creada antes    
                lista.append(linkPublicacion) 

                #Aumentamos el contador
                index += 1 

            #Cuando el contador es igual a la cantidad de elementos en la lista, pasa a este proceso
            else:
                try:
                    #Intentamos buscar el elemento video, si lo encontramos, llegamos al final de la página
                    videos = driver.find_element(by="xpath", value="(//div[@class='x1e56ztr'])[2]")
                    #Por lo tanto, se corta el proceso
                    break
                except:
                    try:
                        #Si no encuentra video, hacemos scroll para mostrar más cédulas y extraer enlaces    
                        scroll(driver)
                    except Exception as e:
                        print(f'Error al hacer scroll: {e}')
                        break
        except Exception as e:
            print(f'Error al encontrar elementos: {e}')
    

def descargarImagen(url, descarga, id, lista):
        """
        Descargamos las imágenes

        Parámetros:
        url(url): link de la imagen a descargar
        descarga(boolean): indicador de True o False sobre si la imagen ya se descargó
        id(int): id del registro
        lista(list): lista para gestionar las descargas

        Retorna:
        lista(list): lista con los valores sobre la imagen ya se descargó o no
        """
        try:
            #Usamos requests para llamar a la url de la imagen
            img = requests.get(url)
            print(url)
            #Si existe la imagen, la descarga
            if img.status_code == 200 and img.headers.get("content-type", "").startswith("image"):
                imagen = Image.open(BytesIO(img.content)) 
                imagen.save(f'cedulas/BC_cedulas/imagenes/{id}.png')
                #Se especifica que la descarga sucedió
                lista.append(True)
            else:
                #Si no, se envía el valor ya existente de la descarga que default es False
                lista.append(descarga)
        
        except:
            lista.append(descarga)
            print('error')
        return lista

def abrirNavegador(website, profile, firefox):
    """
    Abrimos el navegador Firefox configurado para Tor

    Parámetros:
    website(url): url que abriremos
    profile(url): ruta del profile de Tor
    firefox(url): ruta del archivo exe de Tor

    Retorna:
    driver(WebDriver)
    """
    tor_profile_path = profile
    # Configuración de opciones de Firefox
    options = Options()
    options.set_preference('profile', tor_profile_path)
    options.binary_location = firefox

    # Configuración del servicio de GeckoDriver
    service = Service(GeckoDriverManager().install())

    # Inicializar el navegador Firefox con el perfil de Tor
    driver = webdriver.Firefox(service=service, options=options)

    driver.get(website)
    time.sleep(3)
    return driver

def extraccionDatosCedulas(driver, ultimoEnlace, df, columna):
    """
    Extraemos la url de las imágenes y el texto de cada copy

    Parámetros:
    driver(WebDriver)
    ultimoEnlace(url): último enlace que hay en la base de datos de la información extraida
    df(df): data frame con los links de las publicaciones individuales
    """

    #Listas web scraping:
    url = []
    descripciones=[]
    listaUrls=[]
    descargas=[]

    #Definimos variable para manejar los bloqueos de Facebook
    bloqueo = False
    for i, fila in df.iterrows(): #iteramos en la base de datos de los links para abrir uno a uno
        try: 
            link = fila[columna]
            #print(link)
            #Si el link es el mismo que el último link cargado se rompe el ciclo, pues ya actualizamos
            if link == ultimoEnlace: 
                break
            else: #Sino, a descargar todo
                url.append(link) #enviamos ese link a la lista "url"
                #Si no nos ha bloqueado Facebook, seguimos
                if bloqueo == False:
                    driver.get(link) #abrimos el link en el navegador
                    time.sleep(1) #esperamos un segundo a que cargue
                    try:
                        #Si nos bloquea Facebook lo indicamos en la variable
                        inicioSesion = driver.find_element(by='xpath', value='//div[@class="_585r _50f4"]')
                        bloqueo = True
                        print("Pantalla de inicio de sesión detectda")
                        descripciones.append('error al extraer')
                        descargas.append(False)
                        listaUrls.append('error al extraer')
                    except:
                        #Si no hay problemas, continuamos
                        datosImagen = obtenerElementos(driver) #Extraemos toda la información
                        #Agregamos toda la información extraída a las listas 
                        descripciones.append(datosImagen[0]) 
                        listaUrls.append(datosImagen[1])
                        descargas.append(False)
                else:
                    #Si ya nos bloqueó, no intentaremos abrir para no perder tiempo, itera en el resto y coloca error
                    descripciones.append('error al extraer')
                    descargas.append(False)
                    listaUrls.append('error al extraer')

        except Exception as e:
            print(f'Error {e}') #Si pasa algo, lo indicará con la leyenda error
            descripciones.append('no se pudo extraer')
            descargas.append(False)
            listaUrls.append('no se pudo extraer')
            
    print('Proceso 1 finalizado')
    return url, descripciones, listaUrls, descargas

#ACCIÓN

#Definimos la url de la que extraeremos los datos
ruta = 'https://www.facebook.com'
website = f'{ruta}/bc.cebp/photos_by'

profile = "C:/Users/Lauro Rodríguez/Desktop/Tor Browser/Browser/TorBrowser/Data/Browser/profile.default"
firefox = "C:/Users/Lauro Rodríguez/Desktop/Tor Browser/Browser/firefox.exe"

#Abrimos el navegador
driver = abrirNavegador(website, profile, firefox)
#Presionamos las teclas derecha y enter del teclado para cerrar cuadro de diálogo
pyautogui.press('right')
pyautogui.press('enter')
time.sleep(3)

#Damos clic en botón conectar
btnConectar = driver.find_element(by='id', value='connectButton')
btnConectar.click()
time.sleep(30)
try:
    #Si aparece el cuadro de diálogo de cookies, lo manejamos
    btnCookies = driver.find_element(by='xpath', value='//div[@class="x1n2onr6 x1ja2u2z x78zum5 x2lah0s xl56j7k x6s0dn4 xozqiw3 x1q0g3np xi112ho x17zwfj4 x585lrc x1403ito x972fbf xcfux6l x1qhh985 xm0m39n x9f619 xn6708d x1ye3gou xtvsq51 x1r1pt67"]')
    driver.execute_script("arguments[0].click();", btnCookies)
    time.sleep(1)
except:
    pass
#Cerramos el cuadro de diálogo de inicio de sesión
cerrar(driver)
time.sleep(2)

#Definimos una variable vacía que se convertirá en el data frame para almacenar los links de cada publicación
linksImagenes = None
#Definimos la ruta del data frame
linkBase = 'cedulas/BC_cedulas/links_imagenes.csv'
print(f'El df está en: {linkBase}')
#Definimos las columnas
columnas = ['links']
#Lo abrimos o lo creamos
linksImagenes = abrirDf(linksImagenes, linkBase, columnas)

try:
    #Intentamos obtener el último elemento del df
    ultimaImagen = linksImagenes['links'].iloc[0]
except:
    #Si está vacío se maneja "Sin información"
    ultimaImagen = "Sin información"
print(f'El último link es:{ultimaImagen}')

#Generamos la lista a donde enviaremos los links
linksPublicacionesLista = []
#Definimos el contados
index = 0
#Llamamos a la función de extraer enlaces
extraerEnlaces(linksPublicacionesLista, index)

#Convertimos la lista en un data frame
df = pd.DataFrame({'links':linksPublicacionesLista})
#La concatenamos con el data frame inicial de los links y la guardamos
dfLinks = pd.concat([df, linksImagenes], ignore_index=True)
dfLinks.to_csv(linkBase, index=False)

#Creamos una variable vacía que almacerá luego el data frame
datosImagenes = None
#Definimos la ruta para guardar o abrir
linkBase = f'cedulas/BC_cedulas/datos_imagenes.csv'
#Definimos las columnas
columnas = ['id', 'Descripción', 'Url Cédula', 'Link', 'Descarga',
            'Texto', 'Nombre', 'Edad', 'Municipio', 'Colonia', 'Fecha desaparición', 'Estatus', 'Notas']
#Abrimos o creamos el data frame
datosImagenes = abrirDf(datosImagenes, linkBase, columnas)

try:
    #Intentamos acceder al último elemento de la columna Link
    ultimoEnlace = datosImagenes['Link'].iloc[0] #Ubicamos la posición más reciente, el último link cargado a la bd
    print(ultimoEnlace)
except:
    #Si está vacío se manejará "Sin información"
    ultimoEnlace = "Sin información"

valorVacio = None


#Llamamos a la función de extracciónDatosCedulas y enviaremos los valores a las variables
url, descripciones, listaUrls, descargas = extraccionDatosCedulas(driver, ultimoEnlace, dfLinks, 'links')

#Creamos un data frame con la información extraida y valores vacíos en las columnas que aún no necesitamos
df = pd.DataFrame({'id': [valorVacio] * len(descripciones), 
                'Descripción': descripciones,'Url Cédula': listaUrls, 'Link': url, 'Descarga': descargas, 
                'Texto': [valorVacio] * len(descripciones), 'Nombre': [valorVacio] * len(descripciones), 
                'Edad': [valorVacio] * len(descripciones), 'Municipio': [valorVacio] * len(descripciones),
                'Colonia': [valorVacio] * len(descripciones), 
                'Fecha desaparición': [valorVacio] * len(descripciones), 'Estado': [valorVacio] * len(descripciones), 
                'Notas': [valorVacio] * len(descripciones)})

#Concatenamos el data frame inicial con el nuevo y lo guardamos
dfDatosImagenes = pd.concat([df, datosImagenes], ignore_index=True)
dfDatosImagenes.to_csv(linkBase, index=False)

#Le damos una segunda oportunidad a Facebook, con Tor nos cambiará la ip y saldremos del bloqueo
#Filtramos el data frame para encontrar sólo los registros que dicen 'error al extraer'
condicion = dfDatosImagenes['Url Cédula'] == 'error al extraer'
sinInformacion = dfDatosImagenes[condicion]
print(len(sinInformacion))

#Definimos último enlace como valor nulo para que no interfiera en el proceso
ultimoEnlace = None

#Llamamos a la función de extracciónDatosCedulas y enviaremos los valores a las variables
url, descripciones, listaUrls, descargas = extraccionDatosCedulas(driver, ultimoEnlace, sinInformacion, 'Link')
     
#Sustituimos los valores en el data frame y guardamos
dfDatosImagenes.loc[condicion, 'Descripción'] = descripciones
dfDatosImagenes.loc[condicion, 'Url Cédula'] = listaUrls
dfDatosImagenes.loc[condicion, 'Link'] = url
dfDatosImagenes.loc[condicion, 'Descarga'] = descargas

dfDatosImagenes.to_csv(linkBase, index=False)

#Cerramos el navegador
driver.quit()

#Determinar los id
ids = []
totalImagenes = len(dfDatosImagenes)
#Iteramos con un bucle for para integrar los id que serán clave para la descarga
for index, fila in dfDatosImagenes.iterrows():
    id = fila['id']
    if pd.isna(id):
        ids.append(totalImagenes)
        totalImagenes = totalImagenes - 1
    else:
        ids.append(id)
        totalImagenes = totalImagenes-1

dfDatosImagenes['id'] = ids
dfDatosImagenes['id'] = dfDatosImagenes['id'].astype(int)
dfDatosImagenes.to_csv(linkBase, index=False)