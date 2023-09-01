from webdriver_manager.chrome import ChromeDriverManager #para instalar el driver
from selenium.webdriver.chrome.service import Service as ChromeService #para instalar el driver
from selenium import webdriver #Para usar el driver
import pandas as pd 
import time #Importa funcionalidades para esperar a que cargue la página
import requests #Importa funcionalidades para obtener una url (en este caso, para las imágenes)
import re #para caracteres especiales
import datetime #para formatear las fechas
import locale #para que la fecha la lea en español

#Definimos las opciones
options = webdriver.ChromeOptions()
options.add_argument('--headless') #Ocultamos la ventana del navegador, comentamos esta línea si se quiere ver el navegador#options.add_argument('--start-maximized') #Maximizamos la ventana
options.add_argument('--start-maximized') #Maximizamos la ventana

root = 'https://www.facebook.com'
website = f'{root}/BusquedaJal/photos'
service=ChromeService(ChromeDriverManager().install()) #instalamos el driver
driver = webdriver.Chrome(service=service, options=options) #Configuramos el driver
driver.get(website)


def cerrar(): #Creamos una función para cerrar (sirve para el pop-up de inicio de sesión)
    cerrar = driver.find_element(by='xpath', value='//div[@aria-label="Cerrar"]')
    return cerrar.click()

def get_elements(): #Creamos una función para obtener todo lo que necesitemos de la publicación
   
    try:
        description_element = driver.find_element(by='xpath', value='//div[@class="xyinxu5 x4uap5 x1g2khh7 xkhd6sd"]//span') #Extraemos el copy de la publicación si lo hay
        description = description_element.text
        if description_element.find_elements(by='tag name', value='br'): #Los boletines de otro tipo, tienen saltos de línea, los filtramos para no descargar esas imágenes
            description = ""
    except:
        description=""
    try:
        name = get_name(description) #Extraemos el nombre de la persona buscada
        if name == "Buscan a familiares": #Si lo que se busca es a los familiares, lo especificamos en una nota
            note = name 
            name = "Sin dato"
    except:
        name = ""
    try:
        date = driver.find_element(by='xpath', value='//span[@class="x4k7w5x x1h91t0o x1h9r5lt x1jfb8zj xv2umb2 x1beo9mf xaigb6o x12ejxvf x3igimt xarpa2k xedcshv x1lytzrv x1t2pt76 x7ja8zs x1qrby5j"]//a//span').text #Extremos la fecha de publicación
    except:
        date = ""
    try:
        statusCedula = driver.find_element(by='xpath', value='//div[@class="xyinxu5 x4uap5 x1g2khh7 xkhd6sd"]//span//a').text #Buscamos el #Localizado o #Estamos buscando
        if statusCedula == "#EstamosBuscando" and name != "Sin dato": #Filtramos, si es persona buscada, se pone desaparecido
            status = "#Desaparecido"
        elif name == "Sin dato": #Si se busca a la familia, se especifica que es familia buscada, no la persona
            status = "Familia buscada"
        elif "sin vida" in description: #Si fue localizado sin vida, se especifica
            status = f'{statusCedula} sin vida'
        else: #Si no se cumple nada de lo anterior, entonces la persona está localizada con vida y aparecerá "Localizada"
            status = statusCedula
    except: #Si no es cédula, dirá que no está disponible el status.
        status= "No disponible"
    try:
        img = driver.find_element(by='xpath', value='//div[@data-pagelet="MediaViewerPhoto"]//img[@data-visualcompletion="media-vc-image"]') #Encontramos la imagen
        if description == "": #Si la descripción está vacía, agregará una nota que dice que no es cédula.
            note = "No es cédula"
            imgUrl="" #no extraemos la URL
        elif name == "Sin dato": #Si se busca a la familia, aún extraerá la url de la imagen (esto puede comentarse si se requiere)
            imgUrl = img.get_attribute('src')
        else:
            imgUrl = img.get_attribute('src') #si no se cumple nada de lo anterior, extrar la URL
            note=""
            
    except:
        note= "No es cédula" #Si no encuentra una imagen, especificará que no hay cédula
        

    elements_list = [name, description, date, status, imgUrl, note] #Creamos una lista con todo lo obtenido
    return elements_list

def clean_filename(filename): #Creamos la función para eliminar caracteres especiales (sirve para el dar nombre a la cédula).
    valid_characters = r"[^a-zA-Z0-9-_().áéíóúÁÉÍÓÚ ]" 
    return re.sub(valid_characters, '', filename)

#Se puede limpiar el nombre ya que, aunque en cada publicación pareciera haber una publicación distinta, hay patrones
def get_name(name): #Limpiamos la descripción de la cédula para obtener sólo el nombre
    onlyName = name.split() #Separamos la descripción por espacios y manda a un array
    preName = "" #Aquí mandaremos la descripción iniciando ya con el nombre, con lo previo borrado
         
    if name.startswith("#EstamosBuscando a los familiares") or name.startswith("Te informamos que la familia de"): 
        preName = "Buscan a familiares," 
    elif name.startswith("Te informamos que") or name.startswith("Agradecemos tu colaboración"):
        preName = ' '.join(onlyName[3:]) #Elegimos a partir de qué posición del array hay que mantener, en este caso, desde la posición 3
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
        preName = name
        
    indice_coma = preName.split(',') #separamos por comas la nueva descripción y creamos un nuevo array
    if len(indice_coma) == 1: #Verificamos que haya coma, sino, obtenemos las primeras cuatro palabras
        name = ' '.join(preName.split()[:4])
    else:
        name = ''.join(indice_coma[0]) #Pedimos que borre todo después de la primera coma (posición 0 del array)
    return name


#Inicia la acción  
time.sleep(5) 
cerrar() #Cerramos pop-up de inicio de sesión
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

index = 0 #Index para recorrer en las cédulas
df_post_link = pd.read_csv('cedulas\links.csv') #importamos el df que tiene los links de cada publicación
last_cedula = df_post_link['0'].iloc[0] #Ubicamos la primera posición
#print(last_cedula)

#Iniciamos el ciclo
while 'https://www.facebook.com/BusquedaJal/photos/pb.100064672999223.-2207520000/123545622525393/?type=3' not in df_post_link: #el enlace es el de la última cédula publicada
    cedulas_links = driver.find_elements(by='xpath', value='//div[@class="x1e56ztr"]//a') #Hacemos un array con todas las cédulas
    
    #Condicionamos para determinar cuándo hacer scrolling
    if index < len(cedulas_links):
        cedula_link = cedulas_links[index].get_attribute('href')
        if cedula_link == last_cedula:
            break
        else:
            post_link.append(cedula_link) #Obtenemos el link del post individual de la cédula correspondiente
            print(cedula_link)
            index += 1 
    #scrolling
    else: #Si ya no hay más miniaturas a la vista, hace el scrolling 
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
               
        time.sleep(1) #Despues de cada scrolling esperamos a que cargue
print(len(post_link))
df_links = pd.concat([pd.DataFrame({'0':post_link}), df_post_link], ignore_index=True)
df_links.to_csv('cedulas/links.csv', index=False)

df_data_fb_cedulas = pd.read_csv('cedulas\df_fb_extract.csv')
last_link = df_data_fb_cedulas['Link'].iloc[0]
print(last_link)
#Descargamos la información y las fotos
for link in df_links.itertuples(index=False):
    try: 
        print(link[0])
        if link[0] == last_link:
            break
        else:
            driver.get(link[0])
            url.append(link[0])
            time.sleep(1)
            cedulas_data = get_elements() #Extraemos toda la información
            #Agregamos toda la información extraida a las listas creadas antes del bucle while
            name_list.append(cedulas_data[0])
            description_list.append(cedulas_data[1])
            date_list.append(cedulas_data[2])
            status_list.append(cedulas_data[3])
            imgUrl_list.append(cedulas_data[4])
            note_list.append(cedulas_data[5])
            print(cedulas_data[0]) #Sólo para ver el avance, no es necesario, pero imprime en la terminal el nombre
    except:
        print("error")
        name_list.append("error al descargar")
driver.quit() #Cerramos en navegador
#Creamos la base de datos
df = pd.DataFrame({'Nombre': name_list, 'Fecha de publicación': date_list, 'Descripción': description_list,
                   'Estatus': status_list, 'Notas': note_list, 'Url Cédula': imgUrl_list, 'Link': url})


df_fb_extract = pd.concat([df, df_data_fb_cedulas], ignore_index=True)
new_dates = []
# Configurar el idioma español
locale.setlocale(locale.LC_TIME, "es_ES.utf8")

for date in df_fb_extract["Fecha de publicación"].values:
    date_str = str(date)
    #print(date_str)
    if date_str.endswith("h") or date_str.endswith("min"):
        new_date = datetime.datetime.today().date()
    elif date_str.endswith("d"):
        number_days = int(re.search(r'\d+', date_str).group())
        new_date = datetime.datetime.today().date() - datetime.timedelta(days=number_days)
    elif "a las" in date_str:
        date_without_hour = ' '.join(date_str.split()[:3]) +  " de 2023"
        clean_date = datetime.datetime.strptime(date_without_hour, "%d de %B de %Y")
        new_date = clean_date.strftime("%Y-%m-%d")
    elif len(date_str.split()) == 3:
        date_year = date_str + "de 2023"
        clean_date = datetime.datetime.strptime(date_without_hour, "%d de %B de %Y")
        new_date = clean_date.strftime("%Y-%m-%d")
    else:
        try:
            clean_date = datetime.datetime.strptime(date_str, "%d de %B de %Y")
            new_date = clean_date.strftime("%Y-%m-%d")
        except:
            new_date = date_str
    new_dates.append(new_date)
#print(new_dates)
df_fb_extract['Fecha de publicación']=new_dates


#Descarga de imágenes
downloads = []
for index, row in df_fb_extract.iterrows():
    img = row["Url Cédula"]
    name_float = row["Nombre"]
    status_float = row["Estatus"]
    status = str(status_float)
    imagen_float = row["Imagen"]
    imagen = str(imagen_float)

    if imagen == "nan":
        if name_float == "nan" or img == "nan" or name_float == "Sin dato": #La imagen se descarga sólo si hay texto en la descripción, sino no descarga, ese es el filtro
            downloads.append("no se descargó")
        else:
            img = requests.get(img) #Volvemos a usar la función get y damos index de 4, porque la lista imgUrl esta en posición 5
            filename = clean_filename(f'{name_float} {status}') #Limpiamos el nombre
            try:
                with open(f'cedulas/imagenes/todas/{filename}_{index}.png', 'wb') as file: #descargamos la imagen
                        file.write(img.content)
                        downloads.append("Descargada")
            except:
                print("nos se pudo descargar") #se puede borrar
                downloads.append("no se descargó")
    else:
        downloads.append(imagen)        
        
df_fb_extract["Imagen"] = downloads

#Descargamos la base de datos en un csv
df_fb_extract.to_csv('cedulas/df_fb_extract.csv', index=False)
print(df_fb_extract) #No es necesario, puede comentarse o borrarse
