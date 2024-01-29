#Con las librería selenium conseguimos descargar las cédulas de búsqueda y generar una serie de bases de datos
#con distinto tipo de información útil para distintos análisis, en el caso particular, periodístico.

from webdriver_manager.chrome import ChromeDriverManager #para instalar el driver
from selenium.webdriver.chrome.service import Service as ChromeService #para instalar el driver
from selenium import webdriver #Para usar el driver
import pandas as pd 
import time #Importa funcionalidades para esperar a que cargue la página
import requests #Importa funcionalidades para obtener una url (en este caso, para las imágenes)
import re #para caracteres especiales
import datetime #para formatear las fechas
import locale #para que la fecha la lea en español
from PIL import Image
from io import BytesIO
from urllib.parse import urlparse, urlunparse #para manejo de urls
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from unidecode import unidecode #para eliminar acentos
#para los procesos concurrentes
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, urlunparse
#para conectar Drive
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

#----FUNCIONES----
#Funciones para scrapping
#Al abrir el sitio web nos aparece un formulario de inicio de sesión debemos cerrar
def cerrar(): #Creamos una función para cerrar (sirve para el pop-up de inicio de sesión)
    cerrar = driver.find_element(by='xpath', value='//div[@aria-label="Cerrar"]')
    return cerrar.click()

def scroll():
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")            
    time.sleep(1) 

#Para el web scraping
def obtener_elementos(): 
    try: 
        caja_descripcion = driver.find_element(by='xpath', value='//div[@class="xyinxu5 x4uap5 x1g2khh7 xkhd6sd"]//span') #Extraemos el copy de la publicación si lo hay
        descripcion = caja_descripcion.text
        nota = ""
    except:
        descripcion="Sin información"
        nota = "Sin datos"
    try:
        nombre = obtener_nombre(descripcion) #Extraemos el nombre de la persona buscada, más abajo definimos la función específica
        if nombre == "Buscan a familiares": #Si lo que se busca es a los familiares, lo especificamos en una nota
            nota = nombre #Habrá una columna para anotaciones, ahí especificamos que se buscan a los familiares, no a la persona de la cédula
            
    except:
        nombre = "Sin información"
    try:
        fecha = driver.find_element(by='xpath', value='//span[@class="x4k7w5x x1h91t0o x1h9r5lt x1jfb8zj xv2umb2 x1beo9mf xaigb6o x12ejxvf x3igimt xarpa2k xedcshv x1lytzrv x1t2pt76 x7ja8zs x1qrby5j"]//a//span').text #Extremos la fecha de publicación
    except:
        fecha = "Sin información"
    try:
        estadoCedula = driver.find_element(by='xpath', value='//div[@class="xyinxu5 x4uap5 x1g2khh7 xkhd6sd"]//span//a').text #Buscamos el #Localizado o #Estamosbuscando
        if estadoCedula == "#EstamosBuscando" and nombre != "Sin información": #Filtramos, si es persona buscada, se pone desaparecido
            estado = "#Desaparecido"
        elif nombre == descripcion: #Si se busca a la familia, se especifica que es familia buscada, no la persona
            estado = "Revisar"
        elif "sin vida" in descripcion: #Si fue localizado sin vida, se especifica
            estado = f'{estadoCedula} sin vida'
        else: #Si no se cumple nada de lo anterior, entonces la persona está localizada con vida y aparecerá "Localizada" o "Localizado"
            estado = estadoCedula
    except: #Si no es cédula, dirá que no está disponible el status.
        estado= "Sin información"
    try:
        img =WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//img[@data-visualcompletion="media-vc-image"]'))) #Encontramos la imagen, usamos espera explícita para que siga hasta que encuentre la Url
        try:
            imgUrl = img.get_attribute('src')
        except Exception as e:
            print(f'Error: {e}')
            imgUrl = "Sin información"
            
    except:
        nota= "Revisar" #Si no encuentra una imagen, especificará que no hay cédula
        imgUrl="Sin información"

    lista_elementos = [nombre, descripcion, fecha, estado, imgUrl, nota] #Creamos una lista con todo lo obtenido
    return lista_elementos

#Creamos la función para eliminar caracteres especiales (sirve para el dar nombre a la cédula).
def limpiar_nombre_archivo(nombre_archivo): 
    caracteres_validos = r"[^a-zA-Z0-9-_().áéíóúÁÉÍÓÚ ]" #especificamos qué caracteres serán válidos
    return re.sub(caracteres_validos, '', nombre_archivo) #convertimos los caracteres no válidos en cadenas vacías '', es decir, los eliminamos

#Tratamos de obtener el nombre de una vez
def obtener_nombre(nombre): #esta es la función que usamos dentro de la función get_elements() para limpiar la descripción
    nombre_separado = nombre.split() #Separamos la descripción por espacios
    nombre_previo = "" #será el repositorio del nombre antes del último paso

    #Tras encontrar los patrones de los copy, comenzamos a depurar con las función startswith()    
    if nombre.startswith("#EstamosBuscando a los familiares") or nombre.startswith("Te informamos que la familia de"): #Si se busca a la familia, lo especificamos
        nombre_previo = "Buscan a familiares," 
    elif nombre.startswith("Te informamos que") or nombre.startswith("Agradecemos tu colaboración"): #Para personas localizadas
        nombre_previo = ' '.join(nombre_separado[3:]) #Elegimos a partir de qué posición del array hay que mantener, en este caso, desde la posición 3. Es decir, nos borra las palabras 0, 1 y 2
    elif nombre.startswith("#EstamosBuscando a"):
        nombre_previo = ' '.join(nombre_separado[2:])
    elif nombre.startswith("¿Lo has visto? #EstamosBuscando a") or nombre.startswith("¿La has visto? #EstamosBuscando a") :
        nombre_previo = ' '.join(nombre_separado[5:])
    elif nombre.startswith("¿Lo has visto? Ayúdanos a encontrarlo") or nombre.startswith("¿La has visto? Ayúdanos a encontrarla"):
        nombre_previo = ' '.join(nombre_separado[12:])
    elif nombre.startswith("#EstamosBuscando, si tienes datos"):
        nombre_previo = ' '.join(nombre_separado[13:])
    elif nombre.startswith("#EstamosBuscando si tienes información"):
        nombre_previo= ' '.join(nombre_separado[10:])
    elif nombre.startswith("¿Lo has visto? Si tienes información"):
        nombre_previo = ' '.join(nombre_separado[14:])
    elif nombre.startswith("La última vez que se le vio a"):
        nombre_previo = ' '.join(nombre_separado[8:])
    elif nombre.startswith("Gracias por tu colaboración"):
        nombre_previo = ' '.join(nombre_separado[7:])
    else:
        nombre_previo = nombre #hay copys que inician con el nombre de la persona, esos entran aquí, sin modificación

    #Hay una ventaja en los copys, casi todos después del nombre tiene una coma   
    indice_coma = nombre_previo.split(',') #separamos por comas la nueva descripción
    if len(indice_coma) == 1: #Verificamos que haya coma, sino, obtenemos las primeras cuatro palabras
        nombre = ' '.join(nombre_previo.split()[:4])
    else:
        nombre = ''.join(indice_coma[0]) #Pedimos que borre todo después de la primera coma (posición 0 del array)
    return nombre

#funciones para acceder y escribir en DRIVE
def obtener_credenciales():
    flujo = InstalledAppFlow.from_client_secrets_file(credenciales_ruta, scopes)
    credenciales = flujo.run_local_server(port=0)
    return credenciales

def obtener_servicio():
    credenciales = None

    # Intenta cargar las credenciales desde el archivo token.json
    try:
        credenciales = Credentials.from_authorized_user_file('token.json')
    except FileNotFoundError:
        pass

    # Si no hay credenciales válidas, obtén nuevas credenciales
    if not credenciales or not credenciales.valid:
        credenciales = obtener_credenciales()

        # Guarda las credenciales en el archivo token.json para futuros usos
        with open('token.json', 'w') as token:
            token.write(credenciales.to_json())

    # Construye el servicio de Google Drive
    servicio_drive = build('drive', 'v3', credentials=credenciales)
    return servicio_drive

def subir_imagen_a_drive(nombre_archivo, carpeta_destino):
    servicio = obtener_servicio()

    # Crear metadatos del archivo
    metadatos = {
        'name': nombre_archivo,
        'parents': [carpeta_destino],
    }

    # Subir el archivo a Google Drive
    servicio.files().create(body=metadatos, media_body=nombre_archivo).execute()



#----ACCIONES-----
    
#Definimos las opciones del driver
options = webdriver.ChromeOptions()
#options.add_argument('--headless') #Ocultamos la ventana del navegador, comentamos esta línea si se quiere ver el navegador#options.add_argument('--start-maximized') #Maximizamos la ventana
options.add_argument('--start-maximized') #Maximizamos la ventana

root = 'https://www.facebook.com'
website = f'{root}/BusquedaJal/photos_by'
service=ChromeService(ChromeDriverManager().install()) #instalamos el driver
driver = webdriver.Chrome(service=service, options=options) #Configuramos el driver
driver.get(website)
time.sleep(3)
cerrar()
time.sleep(2)

#Verificamos si ya existe el csv
try:
    links_cedulas = pd.read_csv('cedulas/links_cedulas_jalisco.csv')
except FileNotFoundError: 
    #sino, lo creamos
    columna = ['links']
    links_cedulas = pd.DataFrame(columns=columna)
    links_cedulas.to_csv('cedulas/links_cedulas_jalisco.csv', index=False)
try:
    ultima_cedula = links_cedulas['links'].iloc[0]
    print(ultima_cedula)
except:
    ultima_cedula = 'https://www.facebook.com/BusquedaJal/photos/pb.100064672999223.-2207520000/112464860300136/?type=3'

#Lista
links_publicaciones_lista =[]
index = 0

while True:
    try:
        links_publicaciones = driver.find_elements(by='xpath', value='//div[@class="x1e56ztr"]//a') #Encontramos todas las minitauras de las cédulas
        print(len(links_publicaciones_lista))

        if index < len(links_publicaciones):
            link_publicacion = links_publicaciones[index].get_attribute('href') #extramos el link de la publicación individual de la cédula
            print(link_publicacion)
            print(type(link_publicacion))
                    
            if ultima_cedula == link_publicacion: #Si ese link es el mismo de la primera posición de la base de datos, se corta el bucle, pues ya se actualizó
                break            
        
            links_publicaciones_lista.append(link_publicacion) #Si el link no es el mismo, lo enviamos a la lista post_link creada antes
            index += 1 

        else:
            try:
                scroll()
               
            except Exception as e:
                print(f'Error al hacer scroll: {e}')
                break
    except Exception as e:
        print(f'Error al encontrar elementos: {e}')

df_links_publicaciones = pd.DataFrame({'links':links_publicaciones_lista})
df_links_cedulas = pd.concat([df_links_publicaciones, links_cedulas], ignore_index=True)
df_links_cedulas.to_csv('cedulas/links_cedulas_jalisco.csv', index=False)

#Verificamos si ya existe el nuevo csv
try:
    datos_fb_cedulas = pd.read_csv('cedulas/datos_fb_cedulas_jalisco.csv')
except FileNotFoundError: 
    #sino, lo creamos
    columnas = ['Nombre', 'Fecha de publicación', 'Descripción', 'Estado', 'Notas', 'Url Cédula', 'Link', 'Descarga']
    datos_fb_cedulas = pd.DataFrame(columns=columnas)
    datos_fb_cedulas.to_csv('cedulas/datos_fb_cedulas_jalisco.csv', index=False)

try:
    ultimo_link = datos_fb_cedulas['Link'].iloc[0] #Ubicamos la posición más reciente, el último link cargado a la bd
    print(ultimo_link)
except:
    ultimo_link = "Sin información"

#Listas web scraping:
url = []
nombres=[]
descripciones=[]
fechas=[]
estados=[]
lista_url_imgs=[]
notas=[]
descargas=[]

for link in df_links_cedulas.itertuples(index=False): #iteramos en la base de datos de los links para abrir uno a uno
    try: 
        print(link[0])
        if link[0] == ultimo_link: #Si el link es el mismo que el último link cargado a la base de datos "df_data_fb_cedulas", se rompe el ciclo, pues ya actualizamos
            break
        else: #Sino, a descargar todo
            driver.get(link[0]) #abrimos el link en el navegador
            url.append(link[0]) #enviamos ese link a la lista "url"
            time.sleep(1) #esperamos un segundo a que cargue
            cedulas_data = obtener_elementos() #Extraemos toda la información con la función que creamos antes
            #Recordar lo que retorna la función, una lista con [name, description, date, status, imgUrl, note]

            #Agregamos toda la información extraída a las listas 
            nombres.append(cedulas_data[0]) 
            descripciones.append(cedulas_data[1]) 
            fechas.append(cedulas_data[2])
            estados.append(cedulas_data[3])
            lista_url_imgs.append(cedulas_data[4])
            notas.append(cedulas_data[5])
            descargas.append(False)
            print(f'{cedulas_data[0]} {cedulas_data[2]} {cedulas_data[3]}')
    except:
        print("error") #Si pasa algo, lo indicará con la leyenda error
        nombres.append("error al extraer")
        descripciones.append("error al extraer")
        fechas.append("error al extraer")
        estados.append("error al extraer")
        lista_url_imgs.append("error al extraer")
        notas.append("error al extraer")
        descargas.append(False)


#driver.quit() #Cerramos en navegador


df = pd.DataFrame({'Nombre': nombres, 'Fecha de publicación': fechas, 'Descripción': descripciones,
                   'Estado': estados, 'Notas': notas, 'Url Cédula': lista_url_imgs, 'Link': url, 'Descarga': descargas})

#Unimos el df con la base de datos "df_data_fb_cedulas" que fue en la que importamos el archivo df_fb_extract.csv
df_datos_fb_cedulas = pd.concat([df, datos_fb_cedulas], ignore_index=True)
df_datos_fb_cedulas.to_csv('cedulas/datos_fb_cedulas_jalisco.csv', index=False)

#Verificamos los casos a revisar para saber si se descargó o no la información
#Primero limpiamos las listas
url.clear()
nombres.clear()
descripciones.clear()
fechas.clear()
estados.clear()
lista_url_imgs.clear()
notas.clear()
descargas.clear()

condicion = df_datos_fb_cedulas['Notas'] == 'Revisar'
filas_a_revisar = df_datos_fb_cedulas[condicion]

#service=ChromeService(ChromeDriverManager().install()) #instalamos el driver
#driver = webdriver.Chrome(service=service, options=options) #Configuramos el driver

for index, fila in filas_a_revisar.iterrows():
    try:
        link = fila['Link']
        print(link)
        driver.get(link) #abrimos el link en el navegador
        url.append(link) #enviamos ese link a la lista "url"
        time.sleep(1) #esperamos un segundo a que cargue
        cedulas_data = obtener_elementos() #Extraemos toda la información con la función que creamos antes
        #Recordar lo que retorna la función, una lista con [name, description, date, status, imgUrl, note]
        
        #Agregamos toda la información extraída a las listas 
        nombres.append(cedulas_data[0]) 
        descripciones.append(cedulas_data[1]) 
        fechas.append(cedulas_data[2])
        estados.append(cedulas_data[3])
        lista_url_imgs.append(cedulas_data[4])
        descargas.append(False)
        if cedulas_data[1] != 'Sin información':
            notas.append(cedulas_data[5])
            print(f'{cedulas_data[0]} {cedulas_data[2]} {cedulas_data[3]}')
        else:
            notas.append('Error, no se pudo extraer')
            print('Error, no se pudo extraer')
    except:
        print("error") #Si pasa algo, lo indicará con la leyenda error
        nombres.append("error al extraer")
        descripciones.append("error al extraer")
        fechas.append("error al extraer")
        estados.append("error al extraer")
        lista_url_imgs.append("error al extraer")
        notas.append("error al extraer")
        descargas.append(False)

driver.quit()

df_datos_fb_cedulas.loc[condicion, 'Nombre'] = nombres
df_datos_fb_cedulas.loc[condicion, 'Fecha de publicación'] = fechas
df_datos_fb_cedulas.loc[condicion, 'Descripción'] = descripciones
df_datos_fb_cedulas.loc[condicion, 'Estado'] = estados
df_datos_fb_cedulas.loc[condicion, 'Notas'] = notas
df_datos_fb_cedulas.loc[condicion, 'Url Cédula'] = lista_url_imgs
df_datos_fb_cedulas.loc[condicion, 'Link'] = url
df_datos_fb_cedulas.loc[condicion, 'Descarga'] = descargas

df_datos_fb_cedulas.to_csv('cedulas/datos_fb_cedulas_jalisco.csv', index=False)

#Damos formato a las fechas
nuevas_fechas = [] #Creamos una lista para las fechas formateadas
# Configuramos el idioma español para las fechas ya que están en formato "31 de agosto" y buscamos "2023-08-31"
locale.setlocale(locale.LC_TIME, "es_ES.utf8")

for fecha in df_datos_fb_cedulas["Fecha de publicación"].values: #iteramos en las fechas
    fecha_str = str(fecha) #convertimos a str el formato de la fecha, pues es float originalmente
    #print(fecha_str)
    if fecha_str.endswith("min"):
        nueva_fecha = datetime.datetime.today().date() #Si dice que la cédula fue publicada hace minutos y horas, asignamos la fecha de hoy
    elif fecha_str.endswith("h"):
        hoy = datetime.datetime.now()
        horas, unidad = fecha_str.split()
        horas_diferencia = int(horas)
        tiempo_diferencia =  hoy - datetime.timedelta(hours=horas_diferencia)
        nueva_fecha = tiempo_diferencia.strftime("%Y-%m-%d")
    elif fecha_str.endswith("d"): #Si dice que fue publicada hace X días, extraemos el número de días para obtener la fecha
        dias_numero = int(re.search(r'\d+', fecha_str).group())
        nueva_fecha = datetime.datetime.today().date() - datetime.timedelta(days=dias_numero)
    elif "a las" in fecha_str: #Si contiene la frase "a las" borramos la frase y lo que está después de ella y agregamos el año
        fecha_sin_hora = ' '.join(fecha_str.split()[:3]) +  " de 2023"
        fecha_limpia = datetime.datetime.strptime(fecha_sin_hora, "%d de %B de %Y")
        nueva_fecha = fecha_limpia.strftime("%Y-%m-%d")
    elif len(fecha_str.split()) == 3: #Si sólo son tres elementos "31 de agosto", por ejemplo, agregamos el año
        anio = fecha_str + "de 2023"
        fecha_limpia = datetime.datetime.strptime(anio, "%d de %B de %Y")
        nueva_fecha = fecha_limpia.strftime("%Y-%m-%d")
    else: #Si está en el formato "31 de agosto de 2023", por ejemplo, sólo obtenemos la fecha en el formato "2023-08-31"
        try:
            fecha_limpia = datetime.datetime.strptime(fecha_str, "%d de %B de %Y")
            nueva_fecha = fecha_limpia.strftime("%Y-%m-%d")
        except:
            nueva_fecha = fecha_str #Para evitar errores, si no hubo modificaciones, igual enviamos todas las fechas a la lista
    nuevas_fechas.append(nueva_fecha)
#print(new_dates)
df_datos_fb_cedulas['Fecha de publicación']=nuevas_fechas #Sustituimos los valores de fecha de publicación en la base de datos, por los de la lista que creamos

#Eliminamos acentos y convertimos a mayúsculas

nombres_mayuscula = []

for index, fila in df_datos_fb_cedulas.iterrows():
    nombre = str(fila['Nombre'])
    #print(nombre)
    sin_acentos = unidecode(nombre)
    mayuscula = sin_acentos.upper()
    #print(mayuscula)
    nombres_mayuscula.append(mayuscula)
    
df_datos_fb_cedulas['Nombre'] = nombres_mayuscula

#Arreglos y limpieza de errores de localización y desaparición, así como nombres
nuevo_estado = []
nuevo_nombre = []

for index, fila in df_datos_fb_cedulas.iterrows():
    estado_actual = str(fila['Estado'])
    descripcion = str(fila['Descripción'])
    nombre_actual = str(fila['Nombre'])
    estado_actual = estado_actual.upper()

    if nombre_actual.endswith('HA'):
        nombre = nombre_actual.replace('HA','')
        nuevo_nombre.append(nombre)
    elif 'HA SIDO #LOCALIZADO' in nombre_actual:
        nombre = nombre_actual.replace('HA SIDO #LOCALIZADO','')
        nuevo_nombre.append(nombre)
    elif 'HA SIDO #LOCALIZADA' in nombre_actual:
        nombre = nombre_actual.replace('HA SIDO #LOCALIZADA','')
        nuevo_nombre.append(nombre)
    elif 'ESCRIBENOS' in nombre_actual:
        nombre = nombre_actual.replace('ESCRIBENOS', '')
        nuevo_nombre.append(nombre)
    elif nombre.endswith('.'):
        nombre = nombre_actual.replace('.', '')
        nuevo_nombre.append(nombre)
    else:
        nuevo_nombre.append(nombre_actual)

    if estado_actual == "SIN INFORMACIÓN":
        if 'Lo has visto' in descripcion:
            estado = 'DESAPARECIDO'
            nuevo_estado.append(estado)
            print(estado)
        elif 'Agradecemos tu colaboración' in descripcion:
            estado = 'LOCALIZADO'
            nuevo_estado.append(estado)
            print(estado)
        else:
            nuevo_estado.append(estado_actual)
    elif '#' in estado_actual:
        estado = estado_actual.replace('#','')
        nuevo_estado.append(estado)
        print(estado)
    else:
        nuevo_estado.append(estado_actual)

df_datos_fb_cedulas['Estado'] = nuevo_estado
df_datos_fb_cedulas['Nombre'] = nuevo_nombre



df_datos_fb_cedulas.to_csv('cedulas/datos_fb_cedulas_jalisco.csv', index=False)
#df_datos_fb_cedulas.to_csv('cedulas/datos_fb_cedulas_jalisco_copia_2.csv', index=False)

# se_busca = df_datos_fb_cedulas['Estado'] == 'DESAPARECIDO'
# df_se_busca = df_datos_fb_cedulas[se_busca]
# desaparecidos = df_se_busca['Notas'] != 'Buscan a familiares'
# df_desaparecidos = df_se_busca[desaparecidos]
# df_desaparecidos.to_csv('cedulas/desaparecidos_jalisco.csv', index=False)

# localizados_general = (df_datos_fb_cedulas['Estado'] == 'LOCALIZADO') | \
#                 (df_datos_fb_cedulas['Estado'] == 'LOCALIZADA') | \
#                 (df_datos_fb_cedulas['Estado'] == 'LOCALIZADO SIN VIDA') | \
#                 (df_datos_fb_cedulas['Estado'] == 'LOCALIZADA SIN VIDA')
# df_localizados_general = df_datos_fb_cedulas[localizados_general]
# localizados = df_localizados_general['Notas'] != 'Buscan a familiares'
# df_localizados = df_localizados_general[localizados]
# df_localizados.to_csv('cedulas/localizados_jalisco.csv', index=False)

#Este código extrae los casos que no corresponden a alguna cédula

# df_no_cedulas = df_datos_fb_cedulas[~df_datos_fb_cedulas.isin(df_desaparecidos)
#                                     & ~df_datos_fb_cedulas.isin(df_localizados)]

# df_no_cedulas = df_no_cedulas.dropna(axis=0, how='all')
# df_no_cedulas.to_csv('cedulas/no_cedulas_jalisco.csv', index= False)


# Ruta al archivo JSON de credenciales descargado para acceder a Drive
credenciales_ruta = 'cedulas\client_secret_388702296994-rkp8m5nlm6g1e4uvrc1l73tof8jd3p02.apps.googleusercontent.com.json'
# Alcance de acceso
scopes = ['https://www.googleapis.com/auth/drive']
# ID de la carpeta en Google Drive donde se guardarán las imágenes
carpeta__desaparecidos = '14ZFjwYZKPiU94tCSztzQd2hmx9OqAH9S'
carpeta_localizados = '18Qb2gWi5ioCBOFn2m8RVsGpQDPyDYQfS'
carpeta_no_cedulas = '1-ZYym1BQ192gwrP23W7UHTAu2MRWqWRg'

def descargar_imagenes(carpeta_destino, total_img):
    try:
        nombre_archivo_local = f'{nombre}_{estado}_{total_img}.jpg'
        nombre_archivo_local = limpiar_nombre_archivo(nombre_archivo_local)
        respuesta = requests.get(url)
        with open(nombre_archivo_local, 'wb') as archivo:
            archivo.write(respuesta.content)
        subir_imagen_a_drive(nombre_archivo_local, carpeta_destino)
        #total_img = total_img - 1
        df_datos_fb_cedulas.loc[index, 'Descarga'] = True
        #descargas.append(True)
    except Exception as e:
        print(f"Error en descarga: {e}")
        #total_img = total_img - 1
        df_datos_fb_cedulas.loc[index, 'Descarga'] = False
        #descargas.append(False)

df_desaparecidos = df_datos_fb_cedulas[(df_datos_fb_cedulas['Estado']=='DESAPARECIDO') \
    & (df_datos_fb_cedulas['Notas'] != 'Buscan a familiares')]
df_localizados = df_datos_fb_cedulas[df_datos_fb_cedulas['Estado'].str.contains('LOCALIZAD', case=False, na=False) \
                                      & (df_datos_fb_cedulas['Notas'] != 'Buscan a familiares')] 
df_no_cedulas = df_datos_fb_cedulas[~df_datos_fb_cedulas.isin(df_desaparecidos) \
                                     & ~df_datos_fb_cedulas.isin(df_localizados)].dropna(axis=0, how='all')

df_desaparecidos.to_csv('cedulas/desaparecidos_jalisco.csv', index=False)
df_localizados.to_csv('cedulas/localizados_jalisco.csv', index=False)
df_no_cedulas.to_csv('cedulas/no_cedulas_jalisco.csv', index= False)

#Ahora sí, descargamos las imágenes
total_desaparecidos = len(df_desaparecidos)
total_localizados = len(df_localizados)
total_no_cedulas = len(df_no_cedulas)
print(f'{total_desaparecidos} {total_localizados} {total_no_cedulas}')

for index, fila in enumerate(df_datos_fb_cedulas.itertuples()):
    url= fila[6]
    print(fila[8])
    descarga = fila[8]
    nombre = fila[1]
    estado = fila[4]
    nota = fila[5]

    if descarga == "False":
        descarga = 0
    descarga = bool(descarga)
    #print(f'{nombre} {estado} {descarga}')


    if not descarga:
        if nota == 'Buscan a familiares':
            descargar_imagenes(carpeta_no_cedulas, total_no_cedulas)
            total_no_cedulas = total_no_cedulas - 1
            print(f'se pudo {total_no_cedulas}')
        else:
            if estado == 'DESAPARECIDO':
                descargar_imagenes(carpeta__desaparecidos, total_desaparecidos)
                total_desaparecidos = total_desaparecidos - 1
                print('se pudo')
            elif 'LOCALIZAD' in estado:
                descargar_imagenes(carpeta_localizados, total_localizados)
                total_localizados = total_localizados - 1
                print('se pudo')
            else:
                descargar_imagenes(carpeta_no_cedulas, total_no_cedulas)
                total_no_cedulas = total_no_cedulas - 1
                print(f'se pudo {total_no_cedulas}')
    else:
        if nota == 'Buscan a familiares':
            total_no_cedulas = total_no_cedulas - 1
            print(total_no_cedulas)
        else:
            if estado == 'DESAPARECIDO':
                total_desaparecidos = total_desaparecidos - 1
                print(total_desaparecidos)
            elif 'LOCALIZAD' in estado:
                total_localizados = total_localizados - 1
                print(total_localizados)
            else:
                total_no_cedulas = total_no_cedulas - 1
                print(total_no_cedulas)

df_datos_fb_cedulas.to_csv('cedulas/datos_fb_cedulas_jalisco.csv', index=False)

