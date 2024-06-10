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
        

def scroll_al_final(driver):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)  # Espera un poco para permitir que el contenido cargue

website = 'https://sg.guanajuato.gob.mx/personas-desaparecidas/'

driver = abrirNavegador(website,5) #Abrimos el sitio web

scroll_al_final(driver)

#Encontramos cada una de las cédulas de personas desaparecidas y las enviamos a listas
ultimoElemento = WebDriverWait(driver, 15).until(
     lambda d: d.find_element(by='xpath', value='(//h5[@class="card-title"])[last()]').text.strip() != "")

alertasAmber = driver.find_elements(by='xpath', value='//div[@id="listadoAmbar"]//div[@data-aos="fade-up"]')
albas = driver.find_elements(by='xpath', value='//div[@id="listadoAlba"]//div[@data-aos="fade-up"]')
generales = driver.find_elements(by='xpath', value='//div[@id="listado"]//div[@data-aos="fade-up"]')

#Cremos listas
nombresLista = []
urlsLista = []
fechasLista = []

extraccionDatos(alertasAmber)
fechasLista.extend(["Sin dato"]*len(alertasAmber))
extraccionDatos(albas)
fechasLista.extend(["Sin dato"]*len(albas))
extraccionDatos(generales)

for cedula in generales:
    boton = cedula.find_element(by='xpath', value='.//button')
    driver.execute_script("arguments[0].click();", boton)
    time.sleep(1)
    fechaTexto = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, './/div[@class="date"]//p')))
    fecha = fechaTexto.text.strip()
    try:
        fechasLista.append(fecha.split()[1])
        print(fecha.strip().split()[1])
    except:
        if fecha == "FECHA":
            fechasLista.append("Sin dato")
        else:
            fechasLista.append(fecha)
        print(fecha)
    
driver.quit()

df = pd.DataFrame({'Nombre': nombresLista,
                   'Fecha': fechasLista,
                   'Link cédula': urlsLista})

df.to_csv('cedulas/Guanajuato/desaparecidos_Guanajuato.csv', index=False)