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

#Definimos las opciones del driver
options = webdriver.ChromeOptions()
options.add_argument('--headless') #Ocultamos la ventana del navegador, comentamos esta línea si se quiere ver el navegador#options.add_argument('--start-maximized') #Maximizamos la ventana
options.add_argument('--start-maximized') #Maximizamos la ventana

root = 'https://www.facebook.com'
website = f'{root}/BusquedaJal/photos'
service=ChromeService(ChromeDriverManager().install()) #instalamos el driver
driver = webdriver.Chrome(service=service, options=options) #Configuramos el driver
driver.get(website)

#Nota, la mayoría de los elementos los buscamos usando xpath

#Al abrir el sitio web nos aparece un formulario de inicio de sesión debemos cerrar
def cerrar(): #Creamos una función para cerrar (sirve para el pop-up de inicio de sesión)
    cerrar = driver.find_element(by='xpath', value='//div[@aria-label="Cerrar"]')
    return cerrar.click()

#Creamos una función para obtener todo lo que necesitemos de la publicación
#En nuestro caso nos interesa: url de la imagen, fecha de publcación, copy e identificador de localización o búsqueda,
#Del copy, además, extraeremos el nombre de la persona.

def get_elements(): 
   
    try: 
        description_element = driver.find_element(by='xpath', value='//div[@class="xyinxu5 x4uap5 x1g2khh7 xkhd6sd"]//span') #Extraemos el copy de la publicación si lo hay
        description = description_element.text
        if description_element.find_elements(by='tag name', value='br'): #Los boletines de otro tipo, tienen saltos de línea, los filtramos para no descargar esas imágenes
            description = "" #la declaramos vacía porque así filtraremos para no descargar esas imágenes que no nos sirven
    except:
        description=""
    try:
        name = get_name(description) #Extraemos el nombre de la persona buscada, más abajo definimos la función específica
        if name == "Buscan a familiares": #Si lo que se busca es a los familiares, lo especificamos en una nota
            note = name #Habrá una columna para anotaciones, ahí especificamos que se buscan a los familiares, no a la persona de la cédula
            name = "Sin dato" #Colocamos sin dato, ya que no publican el nombre de la persona
    except:
        name = ""
    try:
        date = driver.find_element(by='xpath', value='//span[@class="x4k7w5x x1h91t0o x1h9r5lt x1jfb8zj xv2umb2 x1beo9mf xaigb6o x12ejxvf x3igimt xarpa2k xedcshv x1lytzrv x1t2pt76 x7ja8zs x1qrby5j"]//a//span').text #Extremos la fecha de publicación
    except:
        date = ""
    try:
        statusCedula = driver.find_element(by='xpath', value='//div[@class="xyinxu5 x4uap5 x1g2khh7 xkhd6sd"]//span//a').text #Buscamos el #Localizado o #Estamosbuscando
        if statusCedula == "#EstamosBuscando" and name != "Sin dato": #Filtramos, si es persona buscada, se pone desaparecido
            status = "#Desaparecido"
        elif name == "Sin dato": #Si se busca a la familia, se especifica que es familia buscada, no la persona
            status = "Familia buscada"
        elif "sin vida" in description: #Si fue localizado sin vida, se especifica
            status = f'{statusCedula} sin vida'
        else: #Si no se cumple nada de lo anterior, entonces la persona está localizada con vida y aparecerá "Localizada" o "Localizado"
            status = statusCedula
    except: #Si no es cédula, dirá que no está disponible el status.
        status= "No disponible"
    try:
        img = driver.find_element(by='xpath', value='//div[@data-pagelet="MediaViewerPhoto"]//img[@data-visualcompletion="media-vc-image"]') #Encontramos la imagen
        if description == "": #Si la descripción está vacía, agregará una nota que dice que no es cédula.
            note = "No es cédula"
            imgUrl="" #no extraemos la URL
        #elif name == "Sin dato": #Si se busca a la familia, aún extraerá la url de la imagen (esto puede omitirse si se requiere)
            #imgUrl = img.get_attribute('src')
        else:
            imgUrl = img.get_attribute('src') #si no se cumple nada de lo anterior, extrar la URL
            note=""
            
    except:
        note= "No es cédula" #Si no encuentra una imagen, especificará que no hay cédula
        

    elements_list = [name, description, date, status, imgUrl, note] #Creamos una lista con todo lo obtenido
    return elements_list

#Creamos la función para eliminar caracteres especiales (sirve para el dar nombre a la cédula).
def clean_filename(filename): 
    valid_characters = r"[^a-zA-Z0-9-_().áéíóúÁÉÍÓÚ ]" #especificamos qué caracteres serán válidos
    return re.sub(valid_characters, '', filename) #convertimos los caracteres no válidos en cadenas vacías '', es decir, los eliminamos

#Se puede limpiar el nombre ya que, aunque en cada publicación pareciera haber una publicación distinta, hay patrones
#Hubo algunas excepciones, que limpié manual, pero fueron pocas y de las primeras cédulas publicadas.
def get_name(name): #esta es la función que usamos dentro de la función get_elements() para limpiar la descripción
    onlyName = name.split() #Separamos la descripción por espacios
    preName = "" #será el repositorio del nombre antes del último paso

    #Tras encontrar los patrones de los copy, comenzamos a depurar con las función startswith()    
    if name.startswith("#EstamosBuscando a los familiares") or name.startswith("Te informamos que la familia de"): #Si se busca a la familia, lo especificamos
        preName = "Buscan a familiares," 
    elif name.startswith("Te informamos que") or name.startswith("Agradecemos tu colaboración"): #Para personas localizadas
        preName = ' '.join(onlyName[3:]) #Elegimos a partir de qué posición del array hay que mantener, en este caso, desde la posición 3. Es decir, nos borra las palabras 0, 1 y 2
    elif name.startswith("#EstamosBuscando a"):
        preName = ' '.join(onlyName[2:])
    elif name.startswith("¿Lo has visto? #EstamosBuscando a") or name.startswith("¿La has visto? #EstamosBuscando a") :
            preName = ' '.join(onlyName[5:])
    elif name.startswith("¿Lo has visto? Ayúdanos a encontrarlo") or name.startswith("¿La has visto? Ayúdanos a encontrarla"):
        preName = ' '.join(onlyName[12:])
    elif name.startswith("#EstamosBuscando, si tienes datos"):
        preName = ' '.join(onlyName[13:])
    elif name.startswith("#EstamosBuscando si tienes información"):
        preName= ' '.join(onlyName[10:])
    elif name.startswith("¿Lo has visto? Si tienes información"):
        preName = ' '.join(onlyName[14:])
    else:
        preName = name #hay copys que inician con el nombre de la persona, esos entran aquí, sin modificación

    #Hay una ventaja en los copys, casi todos después del nombre tiene una coma   
    indice_coma = preName.split(',') #separamos por comas la nueva descripción
    if len(indice_coma) == 1: #Verificamos que haya coma, sino, obtenemos las primeras cuatro palabras
        name = ' '.join(preName.split()[:4])
    else:
        name = ''.join(indice_coma[0]) #Pedimos que borre todo después de la primera coma (posición 0 del array)
    return name


#Inicia la acción  
time.sleep(3) #Esperamos que cargue 
cerrar() #Cerramos formulario de inicio de sesión
time.sleep(2) #Esperamos 2 segundos para que cargue, si el internet es bueno será antes, si es malo, dará error porque necesita más tiempo

#Creamos las listas donde estará toda la información que irá a un csv
name_list=[]
description_list=[]
date_list=[]
status_list=[]
imgUrl_list=[]
note_list=[]
post_link=[] 
url=[]

#NOTA: Esta versión ya pasó por un proceso previó de creación de bases de datos y sirve para actualizarlas.
#Si se quiere iniciar de cero, recomiendo borrar los registros de la base de datos, pero no el archivo,
#si se borra el archivo, el código requerirá modificaciones. 
#Usar el código de la forma presentada ahorra tiempo, pues sólo descarga y extrae lo necesario para actualizar y no 
#se requiere iniciar de cero cada vez
#La base de datos "links.csv", la creamos haciendo scroll en el website. Es decir, en lugar de abrir y cerrar
#publicación por publicación para extraer el contenido, primero recorremos todo y extraemos los links individuales 
#de cada publicación donde están las cédulas.

df_post_link = pd.read_csv('cedulas\links.csv') #importamos el df que tiene los links de cada publicación
last_cedula = df_post_link['0'].iloc[0] #Ubicamos la primera posición de la base de datos
print(last_cedula)
index = 0 #Index para recorrer en las cédulas
#Iniciamos el ciclo
while 'https://web.facebook.com/BusquedaJal/photos/pb.100064672999223.-2207520000/123545622525393/?type=3' not in df_post_link: #el enlace es el de la primera cédula que publicó la Comisión de Búsqueda, en febrero de 2020
    cedulas_links = driver.find_elements(by='xpath', value='//div[@class="x1e56ztr"]//a') #Encontramos todas las minitauras de las cédulas
    print(len(cedulas_links))
    cedula_link = cedulas_links[index].get_attribute('href') #extramos el link de la publicación individual de la cédula
    if last_cedula == cedula_link: #Si ese link es el mismo de la primera posición de la base de datos, se corta el bucle, pues ya se actualizó
        break
    else:
        post_link.append(cedula_link) #Si el link no es el mismo, lo enviamos a la lista post_link creada antes
        #print(cedula_link)
        index += 1 
    if index < len(cedulas_links): #comparamos la variable index con la cantidad de miniaturas encontradas
        
        print(cedula_link)
        print(type(cedula_link))
        print(type(last_cedula))
        
    #scroll
    else: #Si ya no hay más miniaturas a la vista, hace el scroll
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")            
        time.sleep(1) #Despues de cada scroll esperamos a que cargue
print(len(post_link))

#Enviamos los datos de la lista post_link a la base de datos links
df_links = pd.concat([pd.DataFrame({'0':post_link}), df_post_link], ignore_index=True)
df_links.to_csv('cedulas/links.csv', index=False) #Guardamos la actualización en el archivo csv

#Importamos la base de datos donde actualizaremos la información extraida de cada publicación individual de cédulas
#NOTA: mismo caso que con la base de datos "links.csv".
df_data_fb_cedulas = pd.read_csv('cedulas\df_fb_extract.csv')
last_link = df_data_fb_cedulas['Link'].iloc[0] #Ubicamos la posición más reciente, el último link cargado a la bd
print(last_link)

#Descargamos la información, pero no las fotos
for link in df_links.itertuples(index=False): #iteramos en la base de datos de los links para abrir uno a uno
    try: 
        print(link[0])
        if link[0] == last_link: #Si el link es el mismo que el último link cargado a la base de datos "df_data_fb_cedulas", se rompe el ciclo, pues ya actualizamos
            break
        else: #Sino, a descargar todo
            driver.get(link[0]) #abrimos el link en el navegador
            url.append(link[0]) #enviamos ese link a la lista "url"
            time.sleep(1) #esperamos un segundo a que cargue
            cedulas_data = get_elements() #Extraemos toda la información con la función que creamos antes
            #Recordar lo que retorna la función, una lista con [name, description, date, status, imgUrl, note]

            #Agregamos toda la información extraída a las listas 
            name_list.append(cedulas_data[0]) 
            description_list.append(cedulas_data[1]) 
            date_list.append(cedulas_data[2])
            status_list.append(cedulas_data[3])
            imgUrl_list.append(cedulas_data[4])
            note_list.append(cedulas_data[5])
            #print(cedulas_data[0])
    except:
        print("error") #Si pasa algo, lo indicará con la leyenda error
        name_list.append("error al extraer")
driver.quit() #Cerramos en navegador
#Creamos la base de datos
df = pd.DataFrame({'Nombre': name_list, 'Fecha de publicación': date_list, 'Descripción': description_list,
                   'Estatus': status_list, 'Notas': note_list, 'Url Cédula': imgUrl_list, 'Link': url})

#Unimos el df con la base de datos "df_data_fb_cedulas" que fue en la que importamos el archivo df_fb_extract.csv
df_fb_extract = pd.concat([df, df_data_fb_cedulas], ignore_index=True)
df_fb_extract.to_csv('cedulas/df_fb_extract.csv', index=False)

new_dates = [] #Creamos una lista para las fechas formateadas
# Configuramos el idioma español para las fechas ya que están en formato "31 de agosto" y buscamos "2023-08-31"
locale.setlocale(locale.LC_TIME, "es_ES.utf8")

for date in df_fb_extract["Fecha de publicación"].values: #iteramos en las fechas
    date_str = str(date) #convertimos a str el formato de la fecha, pues es float originalmente
    #print(date_str)
    if date_str.endswith("min"):
        new_date = datetime.datetime.today().date() #Si dice que la cédula fue publicada hace minutos y horas, asignamos la fecha de hoy
    elif date_str.endswith("h"):
        today = datetime.datetime.now()
        hours, unidad = date_str.split()
        hours_diference = int(hours)
        time_diference =  today - datetime.timedelta(hours=hours_diference)
        new_date = time_diference.strftime("%Y-%m-%d")
    elif date_str.endswith("d"): #Si dice que fue publicada hace X días, extraemos el número de días para obtener la fecha
        number_days = int(re.search(r'\d+', date_str).group())
        new_date = datetime.datetime.today().date() - datetime.timedelta(days=number_days)
    elif "a las" in date_str: #Si contiene la frase "a las" borramos la frase y lo que está después de ella y agregamos el año
        date_without_hour = ' '.join(date_str.split()[:3]) +  " de 2023"
        clean_date = datetime.datetime.strptime(date_without_hour, "%d de %B de %Y")
        new_date = clean_date.strftime("%Y-%m-%d")
    elif len(date_str.split()) == 3: #Si sólo son tres elementos "31 de agosto", por ejemplo, agregamos el año
        date_year = date_str + "de 2023"
        clean_date = datetime.datetime.strptime(date_without_hour, "%d de %B de %Y")
        new_date = clean_date.strftime("%Y-%m-%d")
    else: #Si está en el formato "31 de agosto de 2023", por ejemplo, sólo obtenemos la fecha en el formato "2023-08-31"
        try:
            clean_date = datetime.datetime.strptime(date_str, "%d de %B de %Y")
            new_date = clean_date.strftime("%Y-%m-%d")
        except:
            new_date = date_str #Para evitar errores, si no hubo modificaciones, igual enviamos todas las fechas a la lista
    new_dates.append(new_date)
#print(new_dates)
df_fb_extract['Fecha de publicación']=new_dates #Sustituimos los valores de fecha de publicación en la base de datos, por los de la lista que creamos
df_fb_extract.to_csv('cedulas/df_fb_extract.csv', index=False)

#Ahora sí, descargamos las imágenes
downloads = [] #creamos una lista que nos servirá para actualizar
total_img = len(df_fb_extract)
print(total_img)
service=ChromeService(ChromeDriverManager().install()) #instalamos el driver
driver = webdriver.Chrome(service=service, options=options) #Configuramos el driver
for index, row in df_fb_extract.iterrows(): #iteramos en la base de datos "df_fb_extract" y elegimos las columnas que necesitamos
    img = row["Url Cédula"]
    name_float = row["Nombre"] 
    status_float = row["Estatus"]
    status = str(status_float)
    imagen_float = row["Imagen"] #En esta columna se especifica si la imagen ya fue descargada o no
    imagen = str(imagen_float)
    link = row["Link"]

    if imagen == "nan": #Si la columna imagen tiene valor "nan", quiere decir que falta por descargar esa imagen
        if name_float == "" or img == "" or name_float == "Sin dato": #La imagen se descarga sólo si hay texto en la descripción, sino no descarga, ese es el filtro
            downloads.append("no se descargó")
            total_img=total_img-1
        else:
            try: 
                img = requests.get(img) #obtenemos la url de cada imagen, esto ya es sin selenium para acelerar el proceso
                if img.status_code == 200 and img.headers.get("content-type", "").startswith("image"):
                    print(name_float)
                    final_image = Image.open(BytesIO(img.content))
                    filename = clean_filename(f'{name_float} {status}') #Limpiamos el nombre
                    final_image.save(f'cedulas/imagenes/todas/{filename}_{total_img}.png')
                    downloads.append("Descargada")
                    total_img=total_img-1
                else:
                    print(name_float)
                    print(img)
                    
                    driver.get(link)
                    time.sleep(1)
                    new_img = driver.find_element(by='xpath', value='//div[@data-pagelet="MediaViewerPhoto"]//img[@data-visualcompletion="media-vc-image"]') #Encontramos la imagen
                    new_url = new_img.get_attribute('src')
                    print(new_url)
                    df_fb_extract.at[index,"Url Cédula"] = new_url
                    #print(df_fb_extract.head(5))
                    new_url = requests.get(new_url)
                    final_image = Image.open(BytesIO(new_url.content))
                    filename = clean_filename(f'{name_float} {status}') #Limpiamos el nombre
                    final_image.save(f'cedulas/imagenes/todas/{filename}_{total_img}.png')
                    downloads.append("Descargada")
                    total_img=total_img-1
                    df_fb_extract.to_csv('cedulas/df_fb_extract.csv', index=False)
            except:
                  print("no se pudo descargar") 
                  downloads.append("no se descargó")  
                  total_img=total_img-1
    else:
        downloads.append(imagen) #Si no dice "nan" el valor de imagen, quiere decir que a partir de ahí ya están en la carpeta las cédulas, pero igual enviamos el valor de la casilla para evitar errores.      
        
df_fb_extract["Imagen"] = downloads #Sustituimos la columna "Imagen" en la base de datos df_fb_extract por la lista downloads
driver.quit()
#Descargamos la base de datos en un csv
df_fb_extract.to_csv('cedulas/df_fb_extract.csv', index=False)
#print(df_fb_extract)
