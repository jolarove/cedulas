from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium import webdriver 
import pandas as pd 
import time
import requests 
import re #para caracteres especiales
import datetime #para formatear las fechas
import locale #para que la fecha la lea en español
from PIL import Image
from io import BytesIO
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from unidecode import unidecode #para eliminar acentos
from pytesseract import * #para leer el texto en las imágenes

#FUNCIONES
def cerrar(): #Creamos una función para cerrar (sirve para el pop-up de inicio de sesión)
    cerrar = driver.find_element(by='xpath', value='//div[@aria-label="Cerrar"]')
    return cerrar.click()

def scroll():
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")            
    time.sleep(1) 

def obtenerElementos(): 
    try: 
        caja_descripcion = driver.find_element(by='xpath', value='//div[@class="xyinxu5 x4uap5 x1g2khh7 xkhd6sd"]//span') #Extraemos el copy de la publicación si lo hay
        descripcion = caja_descripcion.text
    except:
        descripcion="Sin información"
    try:
        fecha = driver.find_element(by='xpath', value='//span[@class="x4k7w5x x1h91t0o x1h9r5lt x1jfb8zj xv2umb2 x1beo9mf xaigb6o x12ejxvf x3igimt xarpa2k xedcshv x1lytzrv x1t2pt76 x7ja8zs x1qrby5j"]//a//span').text #Extremos la fecha de publicación
    except:
        fecha = "Sin información"
    try:
        img =WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//img[@data-visualcompletion="media-vc-image"]'))) #Encontramos la imagen, usamos espera explícita para que siga hasta que encuentre la Url
        try:
            imgUrl = img.get_attribute('src')
        except Exception as e:
            print(f'Error: {e}')
            imgUrl = "Sin información"
    except:
        imgUrl="Sin información"

    lista_elementos = [descripcion, fecha, imgUrl] #Creamos una lista con todo lo obtenido
    return lista_elementos

def abrirDf(nombre, link, columnas):
    #Verificamos si ya existe el csv
    try:
        nombre = pd.read_csv(link)
    except FileNotFoundError: 
        #sino, lo creamos
        nombre = pd.DataFrame(columns=columnas)
        nombre.to_csv(link, index=False)
    return nombre

def extraerEnlaces(lista, index):
    while True:
        try:
            linksPublicaciones = driver.find_elements(by='xpath', value='(//div[@class="x1e56ztr"])[1]//a') #Encontramos todas las minitauras de las cédulas
            print(len(linksPublicaciones))

            if index < len(linksPublicaciones):
                linkPublicacion = linksPublicaciones[index].get_attribute('href') #extramos el link de la publicación individual de la cédula
                print(linkPublicacion)
                print(type(linkPublicacion))
                        
                if ultimaImagen == linkPublicacion: #Si ese link es el mismo de la primera posición de la base de datos, se corta el bucle, pues ya se actualizó
                    break            
            
                lista.append(linkPublicacion) #Si el link no es el mismo, lo enviamos a la lista post_link creada antes
                index += 1 

            else:
                try:
                    videos = driver.find_element(by="xpath", value="(//div[@class='x1e56ztr'])[2]")
                    break
                except:
                    try:    
                        scroll()
                    except Exception as e:
                        print(f'Error al hacer scroll: {e}')
                        break
        except Exception as e:
            print(f'Error al encontrar elementos: {e}')
    return lista

def descargarImagen(url, descarga, id, lista, estado):
        try:
            img = requests.get(url)
            print(url)
            if img.status_code == 200 and img.headers.get("content-type", "").startswith("image"):
                imagen = Image.open(BytesIO(img.content)) 
                imagen.save(f'cedulas/{estado}/imagenes/{id}.png')
                lista.append(True)
            else:
                lista.append(descarga)
        
        except:
            lista.append(descarga)
            print('error')
        return lista

#ACCIÓN



ruta = 'https://www.facebook.com'

webs = {
    'Jalisco': '/BusquedaJal/photos_by',
    'Tamaulipas': '/profile.php?id=100064843414092&sk=photos_by',
    'Ciudad de México': '/cbusquedacdmx/photos_by',
    'Veracruz': '/CEBVeracruz/photos_by',
    'Nuevo León': '/CLDBPNL/photos_by'
    }

for estado, url in webs.items():
    opciones = webdriver.ChromeOptions()
    #opciones.add_argument('--headless')
    opciones.add_argument('--start-maximized')
    servicio = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servicio, options=opciones)
    website = f'{ruta}{url}'
    driver.get(website)
    time.sleep(2)
    cerrar()
    time.sleep(2)
    
    linksImagenes = None
    linkBase = f'cedulas/{estado}/links_imagenes.csv'
    print(f'El df está en: {linkBase}')
    columnas = ['links']
    linksImagenes = abrirDf(linksImagenes, linkBase, columnas)

    try:
        ultimaImagen = linksImagenes['links'].iloc[0]
        
    except:
        ultimaImagen = "Sin información"
    print(f'El último link es:{ultimaImagen}')

    linksPublicacionesLista = []
    index = 0
    extraerEnlaces(linksPublicacionesLista, index)


    df = pd.DataFrame({'links':linksPublicacionesLista})
    dfLinks = pd.concat([df, linksImagenes], ignore_index=True)
    dfLinks.to_csv(linkBase, index=False)

    datosImagenes = None
    linkBase = f'cedulas/{estado}/datos_imagenes.csv'
    columnas = ['id', 'Fecha de publicación', 'Descripción', 'Url Cédula', 'Link', 'Descarga',
                'Texto', 'Nombre', 'Edad', 'Municipio', 'Colonia', 'Fecha Desaparición', 'Estado', 'Notas']

    datosImagenes = abrirDf(datosImagenes, linkBase, columnas)

    try:
        ultimoEnlace = datosImagenes['Link'].iloc[0] #Ubicamos la posición más reciente, el último link cargado a la bd
        print(ultimoEnlace)
    except:
        ultimoEnlace = "Sin información"

    #Listas web scraping:
    url = []
    descripciones=[]
    fechas=[]
    listaUrls=[]
    descargas=[]

    valorVacio = None
    for link in dfLinks.itertuples(index=False): #iteramos en la base de datos de los links para abrir uno a uno
        try: 
            #print(link[0])
            if link[0] == ultimoEnlace: #Si el link es el mismo que el último link cargado a la base de datos "df_data_fb_cedulas", se rompe el ciclo, pues ya actualizamos
                break
            else: #Sino, a descargar todo
                driver.get(link[0]) #abrimos el link en el navegador
                url.append(link[0]) #enviamos ese link a la lista "url"
                time.sleep(1) #esperamos un segundo a que cargue
                datosImagen = obtenerElementos() #Extraemos toda la información con la función que creamos antes
                #Recordar lo que retorna la función, una lista con [name, description, date, status, imgUrl, note]

                #Agregamos toda la información extraída a las listas 
                descripciones.append(datosImagen[0]) 
                fechas.append(datosImagen[1])
                listaUrls.append(datosImagen[2])
                descargas.append(False)
                print(f'todo correcto: {datosImagen[1]}')
        except:
            print("error al extraer") #Si pasa algo, lo indicará con la leyenda error
            descripciones.append("error al extraer")
            fechas.append("error al extraer")
            listaUrls.append("error al extraer")
            descargas.append(False)
                

    df = pd.DataFrame({'id': [valorVacio] * len(descripciones), 'Fecha de publicación': fechas, 
                    'Descripción': descripciones,'Url Cédula': listaUrls, 'Link': url, 'Descarga': descargas, 
                    'Texto': [valorVacio] * len(descripciones), 'Nombre': [valorVacio] * len(descripciones), 
                    'Edad': [valorVacio] * len(descripciones), 'Municipio': [valorVacio] * len(descripciones),
                    'Colonia': [valorVacio] * len(descripciones), 
                    'Fecha desaparición': [valorVacio] * len(descripciones), 'Estado': [valorVacio] * len(descripciones), 
                    'Notas': [valorVacio] * len(descripciones)})

    #Unimos el df con la base de datos "df_data_fb_cedulas" que fue en la que importamos el archivo df_fb_extract.csv
    dfDatosImagenes = pd.concat([df, datosImagenes], ignore_index=True)
    dfDatosImagenes.to_csv(linkBase, index=False)

    url.clear()
    descripciones.clear()
    fechas.clear()
    listaUrls.clear()
    descargas.clear()


    condicion = dfDatosImagenes['Url Cédula'] == 'Sin información'
    sinInformacion = dfDatosImagenes[condicion]

    for index, fila in sinInformacion.iterrows():
        try:
            enlace = fila['Link']
            print(enlace)
            driver.get(enlace)
            url.append(enlace)
            time.sleep(1)
            datosImagen = obtenerElementos()
            descripciones.append(datosImagen[0]) 
            fechas.append(datosImagen[1])
            listaUrls.append(datosImagen[2])
            descargas.append(False)
            print(f'{datosImagen[2]}')
        except:
            print('error al extraer')
            descripciones.append("error al extraer")
            fechas.append("error al extraer")
            listaUrls.append("error al extraer")
            descargas.append(False)

    dfDatosImagenes.loc[condicion, 'Descripción'] = descripciones
    dfDatosImagenes.loc[condicion, 'Fecha de publicación'] = fechas
    dfDatosImagenes.loc[condicion, 'Url Cédula'] = listaUrls
    dfDatosImagenes.loc[condicion, 'Link'] = url
    dfDatosImagenes.loc[condicion, 'Descarga'] = descargas

    dfDatosImagenes.to_csv(linkBase, index=False)


    driver.close()

    #Damos formato a las fechas
    nuevasFechas = [] #Creamos una lista para las fechas formateadas
    # Configuramos el idioma español para las fechas ya que están en formato "31 de agosto" y buscamos "2023-08-31"
    locale.setlocale(locale.LC_TIME, "es_ES.utf8")
    anioActual = 2024

    for fecha in dfDatosImagenes["Fecha de publicación"].values: #iteramos en las fechas
        fechaStr = str(fecha) #convertimos a str el formato de la fecha, pues es float originalmente
        #print(fecha_str)
        if fechaStr.endswith("min"):
            nuevaFecha = datetime.datetime.today().date() #Si dice que la cédula fue publicada hace minutos y horas, asignamos la fecha de hoy
        elif fechaStr.endswith("h"):
            hoy = datetime.datetime.now()
            horas, unidad = fechaStr.split()
            horasDiferencia = int(horas)
            tiempoDiferencia =  hoy - datetime.timedelta(hours=horasDiferencia)
            nuevaFecha = tiempoDiferencia.strftime("%Y-%m-%d")
        elif fechaStr.endswith("d"): #Si dice que fue publicada hace X días, extraemos el número de días para obtener la fecha
            diasNumero = int(re.search(r'\d+', fechaStr).group())
            nuevaFecha = datetime.datetime.today().date() - datetime.timedelta(days=diasNumero)
        elif "a las" in fechaStr: #Si contiene la frase "a las" borramos la frase y lo que está después de ella y agregamos el año
            fechaSinHora = ' '.join(fechaStr.split()[:3]) +  f" de {anioActual}"
            fechaLimpia = datetime.datetime.strptime(fechaSinHora, "%d de %B de %Y")
            nuevaFecha = fechaLimpia.strftime("%Y-%m-%d")
        elif len(fechaStr.split()) == 3: #Si sólo son tres elementos "31 de agosto", por ejemplo, agregamos el año
            anio = fechaStr + f" de {anioActual}"
            fechaLimpia = datetime.datetime.strptime(anio, "%d de %B de %Y")
            nuevaFecha = fechaLimpia.strftime("%Y-%m-%d")
        else: #Si está en el formato "31 de agosto de 2023", por ejemplo, sólo obtenemos la fecha en el formato "2023-08-31"
            try:
                fechaLimpia = datetime.datetime.strptime(fechaStr, "%d de %B de %Y")
                nuevaFecha = fechaLimpia.strftime("%Y-%m-%d")
            except:
                nuevaFecha = fechaStr #Para evitar errores, si no hubo modificaciones, igual enviamos todas las fechas a la lista
        nuevasFechas.append(nuevaFecha)
    #print(new_dates)
    dfDatosImagenes['Fecha de publicación'] = nuevasFechas #Sustituimos los valores de fecha de publicación en la base de datos, por los de la lista que creamos
    dfDatosImagenes.to_csv(linkBase, index=False)

    #Determinar los id
    ids = []
    totalImagenes = len(dfDatosImagenes)
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

    #Descarga de imágenes
    descargas.clear()
    totalImagenes = len(dfDatosImagenes)
    print(totalImagenes)

    condicion = dfDatosImagenes['Descarga'] == 0
    descargar = dfDatosImagenes[condicion]

    for index, fila in descargar.iterrows():
        url = fila['Url Cédula']
        descarga = fila['Descarga']
        id = fila['id']
        print(id)
        descargarImagen(url, descarga, id, descargas, estado)

    dfDatosImagenes.loc[condicion, 'Descarga'] = descargas

    dfDatosImagenes.to_csv(linkBase, index=False)

    # #Extraer el texto

    # pytesseract.tesseract_cmd = r'C:/Users/User/AppData/Local/Programs/Tesseract-OCR/tesseract.exe'



    # def extraerTexto(carpeta, id):
    #     rutaImg = f'{carpeta}/{id}.png'
    #     imagen = Image.open(rutaImg)
    #     try:
    #         imgBn = imagen.convert('L')
    #     except:
    #         textoExtraido = 'Sin texto'
    #     try:
    #         textoExtraido = pytesseract.image_to_string(imgBn)
    #         if not textoExtraido.strip():  # Verifica si la cadena está vacía
    #             textoExtraido = "Sin texto"
    #         print(textoExtraido)
    #     except:
    #         textoExtraido = 'Sin texto'
    #         print(textoExtraido)
    #     return textoExtraido

    # condicion = ~pd.notna(dfDatosImagenes['Texto'])
    # extraccion = dfDatosImagenes[condicion]
    # print(len(extraccion))

    # carpeta = f'cedulas/{estado}/imagenes'
    # print(carpeta)
    # textos = []


    # for index, fila in extraccion.iterrows():
    #     textoImagen = fila['Texto']
    #     print(textoImagen)
    #     id = fila['id']
    #     # if "." in id:
    #     #     id = id.split(".")[0]
    #     print(id)
    #     textoExtraido = extraerTexto(carpeta, id)
    #     print(id)
    #     textos.append(textoExtraido)

    # dfDatosImagenes.loc[condicion, 'Texto'] = textos
    # dfDatosImagenes.to_csv(linkBase, index=False)

driver.quit()
# def extraerDatos(texto):
#     texto = texto.upper()
#     patrones = {
#         'nombre': r'NOMBRE:\s*(.*)',
#         'edad': r'EDAD:\s*(.*)',
#         'colonia': r'VEZ:\s*(.*)',
#         'fechaDesaparicion': r'FECHA:\s*(.*)',
#         'municipio': r'LUGAR:\s*(.*)'
#     }
#     elementos = {}
    
#     for dato, patron in patrones.items():
#         try:
#             resultado = re.search(patron, texto)
#             elementos[dato] = resultado.group(1) if resultado else 'No disponible'
#         except AttributeError:
#             elementos[dato] = 'No disponible'
    
#     return elementos

# nombres = []
# edades = []
# municipios = []
# colonias = []
# fechasDesaparicion = []
# estados = []
# notas = []

# for index, fila in dfDatosImagenes.iterrows():
#     texto = fila['Texto']
#     elementos = extraerDatos(texto)
#     nombres.append(elementos['nombre'])
#     edades.append(elementos['edad'])
#     colonias.append(elementos['colonia'])
#     municipios.append(elementos['municipio'])
#     fechasDesaparicion.append(elementos['fechaDesaparicion'])
#     #print(elementos)

# dfDatosImagenes['Nombre'] = nombres
# dfDatosImagenes['Edad'] = edades
# dfDatosImagenes['Municipio'] = municipios
# dfDatosImagenes['Colonia'] = colonias
# dfDatosImagenes['Fecha desaparición'] = fechasDesaparicion

# dfDatosImagenes.to_csv('cedulas/jalisco/datos_imagenes.csv', index=False)
