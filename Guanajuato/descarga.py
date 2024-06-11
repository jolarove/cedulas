#Usamos la biblioteca Selenium para navegar y desvcargar los datos automáticamente
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium import webdriver 
import pandas as pd
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


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

#Generamos la función dado que el ciclo for lo necesitaremos más una vez
def extraccionDatos(lista):
    for elemento in lista:
        nombre = elemento.find_element(by="xpath", value='.//h5').text
        urlImg = elemento.find_element(by="xpath", value='.//img').get_attribute('src')
        nombresLista.append(nombre)
        print(nombre)
        urlsLista.append(urlImg)
        
#Función para hacer scroll hasta el final de la página. Es necesario para que cargue el contenido
def scroll_al_final(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)  # Espera un poco para permitir que el contenido cargue

website = 'https://sg.guanajuato.gob.mx/personas-desaparecidas/'

driver = abrirNavegador(website,5) #Abrimos el sitio web

scroll_al_final(driver) #Hacemos scroll

#No seguiremos adelante hasta que no cargue el último elemento que necesitamos
#Usamos una función lambda para especificar que espere hasta que el elemento final no esté vacío
ultimoElemento = WebDriverWait(driver, 15).until(
     lambda d: d.find_element(by='xpath', value='(//h5[@class="card-title"])[last()]').text.strip() != "")

#Encontramos cada una de las cédulas de personas desaparecidas y las enviamos a listas
#En Guanajuato están divididas en tres secciones
alertasAmber = driver.find_elements(by='xpath', value='//div[@id="listadoAmbar"]//div[@data-aos="fade-up"]')
albas = driver.find_elements(by='xpath', value='//div[@id="listadoAlba"]//div[@data-aos="fade-up"]')
generales = driver.find_elements(by='xpath', value='//div[@id="listado"]//div[@data-aos="fade-up"]')

#Cremos listas
nombresLista = []
urlsLista = []
fechasLista = []

#Extraemos los datos
extraccionDatos(alertasAmber)
fechasLista.extend(["Sin dato"]*len(alertasAmber)) #No hay fechas en Alerta Amber
extraccionDatos(albas)
fechasLista.extend(["Sin dato"]*len(albas)) #No hay fechas en Protocolo Alba
extraccionDatos(generales)

#Iteramos para extraer las fechas de las cédulas generales que sí cuentan con el dato
for cedula in generales:
    #Es necesario encontrar un botón y presionarlo para extraer
    boton = cedula.find_element(by='xpath', value='.//button') 
    driver.execute_script("arguments[0].click();", boton)
    #Usamos una combinación de esperas para extraer los datos
    fechaTexto = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, './/div[@class="date"]//p')))
    time.sleep(1)
    #Borramos espacios
    fecha = fechaTexto.text.strip()
    try:
        #Si tiene disponible el dato de fecha, lo extraemos
        fechasLista.append(fecha.split()[1]) 
        print(fecha.strip().split()[1])
    except:
        #Sino, colocamos que no hay dato
        if fecha == "FECHA":
            fechasLista.append("Sin dato")
        else:
            fechasLista.append(fecha)
        print(fecha)
    
driver.quit()

#Creamos la base de datos
df = pd.DataFrame({'Nombre': nombresLista,
                   'Fecha': fechasLista,
                   'Link cédula': urlsLista})

#La guardamos en csv
df.to_csv('cedulas/Guanajuato/desaparecidos_Guanajuato.csv', index=False)