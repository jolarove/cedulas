#Usamos la biblioteca Selenium para navegar y desvcargar los datos automáticamente
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium import webdriver 
import pandas as pd
import time

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

website = 'https://version-publica-repd.jalisco.gob.mx/cedulas-de-busqueda'

driver = abrirNavegador(website,5) #Abrimos el sitio web

#Damos clic en el botón buscar para que muestre todas las cédulas y esperamos que cargue
buscar = driver.find_element(by="xpath", 
                             value="//button[@class='MuiButtonBase-root MuiIconButton-root MuiIconButton-sizeMedium css-18mwzm8']")
buscar.click()
time.sleep(10) #si da error, aumentar el tiempo de espera

#creamos las listas donde se almacenarán los datos extraidos
estatus = []
imagenes = []
nombres = []
edades = []
sexos = []
generos =[]
complexiones =[]
estaturas = []
teces = []
cabellos = []
ojos_ced = []
fechas = []
lugares = []
vestimentas = []
senias_des = []

#buscamos el panel de paginación y definimos el límite para el ciclo
paginacion = driver.find_element(by='xpath', value='//ul[@class="MuiPagination-ul css-nhb8h9"]')
paginas = paginacion.find_elements(by='tag name', value='li')
ultimaPagina = int(paginas[-2].text)
paginaActual = 1

#comenzamos la navegación y descargamos todo lo descargable
while paginaActual <= ultimaPagina:
    print(f'{paginaActual} {ultimaPagina}')
    try:
        cajaCedulas = driver.find_element(by='xpath', value='//div[1]/div[1]/div[2]/div/div[2]/div[2]')
        cedulas = cajaCedulas.find_elements(by='xpath', value='.//div[@class="MuiBox-root css-13pkf70"]')
        for cedula in cedulas:
            nombre = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-apx2uo")]//p[contains(@class, "css-445tfr")])[1]').text
            nombres.append(nombre)
            print(nombre)
            estado = cedula.find_element(by='xpath', value='.//p[contains(@class, "css-k2vnwu")]').text
            estatus.append(estado)
            edad = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-apx2uo")]//p[contains(@class, "css-445tfr")])[2]').text
            edades.append(edad)
            sexo = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[1]//td[2]//p)[1]').text
            sexos.append(sexo)
            genero = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[1]//td[4]//p)[1]').text
            generos.append(genero)
            complexion = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[2]//td[2]//p)[1]').text
            complexiones.append(complexion)
            estatura = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[2]//td[4]//p)[1]').text
            estaturas.append(estatura)
            tez = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[3]//td[2]//p)[1]').text
            teces.append(tez)
            cabello = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[3]//td[4]//p)[1]').text
            cabellos.append(cabello)
            ojos = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[4]//td[2]//p)[1]').text
            ojos_ced.append(ojos)
            fecha = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[1]//td[2]//p)[2]').text
            fechas.append(fecha)
            lugar = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[2]//td[2]//p)[2]').text
            lugares.append(lugar)
            vestimenta = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[3]//td[2]//p)[2]').text
            vestimentas.append(vestimenta)
            try:
                senias = cedula.find_element(by='xpath', value='(.//div[contains(@class, "css-1fwfo5s")]//table//tr[4]//td[2]//p)[2]').text
                senias_des.append(senias)
            except:
                  senias_des.append('SIN DATOS')
            img = cedula.find_element(by='xpath', value='.//img[@alt="Imagen"]').get_attribute('src')
            imagenes.append(img)
        #damos clic en el botón siguiente página, siempre y cuando no estemos en la última
        if paginaActual < ultimaPagina:
            botonSiguiente = driver.find_element(by='xpath', value='//li//button[@aria-label="Go to next page"]')
            botonSiguiente.click()
        paginaActual += 1
        time.sleep(1)
        

    except Exception as e:
            print(f'Error: {e}')

#cerramos el navegador web
driver.quit()

#creamos la base de datos con lo extraído de las cédulas de búsqueda
df = pd.DataFrame({'Nombre': nombres, 'Estatus':estatus, 'Fecha desaparición': fechas, 'Lugar': lugares, 'Edad': edades,
                   'Sexo': sexos, 'Género': generos, 'Complexión': complexiones, 'Estatura': estaturas,
                   'Tez': teces, 'Cabello': cabellos, 'Ojos': ojos_ced, 'Vestimenta': vestimentas,
                   'Señas Particulares': senias_des})
#Guardamos la base de datos en formato csv
df.to_csv(f'cedulas/Jalisco/desaparececidos_Jalisco.csv', index=False)