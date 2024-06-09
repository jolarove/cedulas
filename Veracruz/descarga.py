#Este algoritmo realiza una descarga automática de cédulas de búsqueda de estados de México

#Usamos la biblioteca Selenium para navegar y desvcargar los datos automáticamente
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium import webdriver 
import pandas as pd 
#Usamos esta librería para las esperas
import time 
import re

#Con esta función abrimos la página web en un navegador
#Vamos a darle como atributos la url y el tiempo que queremos esperar
def abrirNavegador(website, espera):    
    opciones = webdriver.ChromeOptions()
    #opciones.add_argument('--headless')
    opciones.add_argument('--start-maximized')
    servicio = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servicio, options=opciones)
    driver.get(website)
    time.sleep(espera)
    return driver

#Definimos una función para cerrar un cuadro de diálogo que aparece al inicio
def cerrar(btn):
    btnCerrar = driver.find_element(by='xpath', value=btn)
    btnCerrar.click()
    time.sleep(2)


website = 'https://www.segobver.gob.mx/cebv/busqueda_personas3.php'
espera = 5
driver = abrirNavegador(website, espera) #Abrimos el navegador

btn = '//button[@class="btn btn-outline-secondary"]' #Detectamos el botón y cerramos el cuadro de diálogo
cerrar(btn)

#Definimos las listas para almacenar los datos
nombre = []
fecha = []
imgUrl = []
estatusLista = []

#Buscamos el selector y obtenemos las opciones disponibles para extraer los datos
estatusSelector = driver.find_elements(by='xpath', value='//select[@id="idArea"]//option')

#Con un ciclo for damos clic en cada opción y extraemos los datos
for estatus in estatusSelector:
    estatus.click()
    estado = estatus.text
    print(estado)
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
        print(totalCasos)
    else:
        print('Hubo un error')
        break
    #Definimos una variable para control y saber cuándo romper el ciclo while
    elementosCapturados = 0
    print(elementosCapturados)

    #Con un ciclo while recorremos las páginas disponibles de la tabla donde están los datos
    while elementosCapturados < totalCasos:
        tabla = driver.find_element(by='id', value='tblResult') #Buscamos la tabla
        #Encontramos la información de las filas de la tabla
        casos = tabla.find_elements(by='xpath', value='.//tbody//tr') 

        #Encontramos la información de cada celda y la agrupamos de acuerdo a las columnas
        for caso in casos:
            nombres = caso.find_elements(by='xpath', value='.//td[1]')
            fechas = caso.find_elements(by='xpath', value='.//td[2]')
            imagenes = caso.find_elements(by='xpath', value='.//td[3]')

            #Ahora, iteramos en cada lista de elementos encontrados 
            #para extraer el texto y enviar a nuevas listas
            for elemento in nombres:
                nombre.append(elemento.text)
                if estado == 'No localizadas':
                    estatusLista.append('Desaparecido')
                else:
                    estatusLista.append('Localizado')
                elementosCapturados += 1 #Aumentamos en uno la variable de control para el ciclo while
                print(f'{elemento.text} {elementosCapturados}')
            for elemento in fechas:
                fecha.append(elemento.text)
            for elemento in imagenes:
                try:
                    imagen = elemento.find_element(by='xpath', value='.//a').get_attribute('href')
                except:
                    imagen = 'Sin imagen'
                imgUrl.append(imagen)

        #Encontramos la paginación y damos clic
        if elementosCapturados < totalCasos:
            btnSiguiente = driver.find_element(by='xpath', value='//div[contains(text(), "Sig")]')
            try:
                btnSiguiente.click()
            except:
                driver.execute_script("arguments[0].click();", btnSiguiente)
            time.sleep(1)
        
driver.quit() #Cerramos el navegador

#Creamos la base de datos
df = pd.DataFrame({'Nombre': nombre,
                   'Fecha desaparición': fecha,
                   'Url imagen': imgUrl,
                   'Estatus': estatusLista})
#Guardamos la base de datos en formato csv
df.to_csv('cedulas/Veracruz/desaparecidos_Veracruz.csv', index=False)