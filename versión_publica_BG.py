#Con este algoritmo extraemos los datos de la versión pública del RNPDNO actualizado a diciembre de 2023
#Sólo extraemos la información de los estados que necesitamos: Jalisco, Estado de México, Veracruz,
#Guanajuato, Puebla y Tabasco. 

#Paqueterías necesarias
from webdriver_manager.chrome import ChromeDriverManager 
from selenium.webdriver.chrome.service import Service as ChromeService 
from selenium import webdriver 
import pandas as pd 
import time 
from selenium.common.exceptions import StaleElementReferenceException

#Función para abrir el navegador
def abrirNavegador(website, espera):    
    opciones = webdriver.ChromeOptions()
    #Si queremos ver el proceso de automatización, comentamos la siguiente línea, sino queremos verlo, quitamos el comentario
    #opciones.add_argument('--headless')
    opciones.add_argument('--start-maximized')
    servicio = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servicio, options=opciones)
    driver.get(website)
    time.sleep(espera)
    return driver

website = 'https://busquedageneralizada.gob.mx/consulta/'
espera = 5 #definimos una espera de 5 segundo para que cargue el sitio web

#Llamamos a la función y definimos el driver. Aquí se abre la ventana del navegador
driver = abrirNavegador(website, espera) 

#Lo primero que haremos será determinar bloques de 100 registros y no de 10, como está por default
seleccion = driver.find_element(by='xpath', value='//select[@name="t-busq_length"]//option[@value="100"]')
seleccion.click()
#Damos tres segundos para que cargue el contenido
time.sleep(3)

#Creamos una lista con los estados a extraer y que usaremos para filtrar la información
entidades = ['Jalisco','Estado de Mexico', 'Veracruz', 'Guanajuato', 'Puebla', 'Tabasco']


#Con un bucle for iniciamos el proceso de extracción por cada estado en la lista
for entidad in entidades:
    #Nos dirigimos al buscador y escribimos el nombre del estado para generar el filtro
    entidadBuscar = driver.find_element(by='xpath', value='//input[@type="search"]')
    entidadBuscar.clear() #antes de escribir el nombre del estado, limpiamos el campo para evitar conflictos
    entidadBuscar.send_keys(entidad)
    time.sleep(1) #esperamos a que cargue

    #Buscamos el total de páginas que tiene la tabla de datos
    #Encontramos todos los link de la paginación
    paginacion = driver.find_elements(by='xpath', value='//a[@class="paginate_button "]')
    ultimaPaginaTexto = paginacion[-1].text #Elegimos el último y lo convertimos en texto

    #Eliminamos la coma del número (si la tuviera) y lo convertimos a entero, 
    #pues se extrae como cadena de texto
    ultimaPagina = ultimaPaginaTexto.replace(",", "")
    ultimaPagina = int(ultimaPagina)
    print(ultimaPagina) #Print para control
    #Definimos en cuál página de la tabla estamos
    paginaActual = 1

    #Definimos las listas con todos los datos que extraeremos
    foliosLista = []
    categoriasLista = []
    nombresLista = []
    apellidos1 = []
    apellidos2 = []
    edadesLista = []
    sexosLista = []
    nacionalidadesLista = []
    fechasLista = []
    autoridadesLista =[]
    estadosLista = []

    #Con un bucle while iteramos para extraer la información de la tabla. El bucle parará cuando llegue a la
    #última pagina de la tabla
    while paginaActual <= ultimaPagina:
        tabla = driver.find_element(by='id', value='t-busq') #buscamos la tabla
        desaparecidos = tabla.find_elements(by='xpath', value='.//tbody//tr') #buscamos las filas de la tabla

        #Con un bucle for extraemos iterando sobre las filas de la tabla, genermos listas con los valores de cada columna
        for desaparecido in desaparecidos:
            try:
                folios = desaparecido.find_elements(by='xpath', value='.//td[1]')
                categorias = desaparecido.find_elements(by='xpath', value='.//td[2]') 
                nombres = desaparecido.find_elements(by='xpath', value='.//td[3]')
                primerosApellidos = desaparecido.find_elements(by='xpath', value='.//td[4]')
                segundosApellidos = desaparecido.find_elements(by='xpath', value='.//td[5]')
                edades = desaparecido.find_elements(by='xpath', value='.//td[6]')
                sexos = desaparecido.find_elements(by='xpath', value='.//td[7]')
                nacionalidades = desaparecido.find_elements(by='xpath', value='.//td[8]')
                fechas = desaparecido.find_elements(by='xpath', value='.//td[9]')
                autoridades = desaparecido.find_elements(by='xpath', value='.//td[10]')
                estados = desaparecido.find_elements(by='xpath', value='.//td[11]')

                #Ahora, con bucles for, extraemos los valores individuales y los enviamos a las listas
                for elemento in folios:
                    foliosLista.append(elemento.text)
                for elemento in categorias:
                    #hay elementos que están dentro de un botón y otros que no lo tienen, por eso, las líneas adicionales
                    try:
                        categoria = elemento.find_element(by='xpath', value='.//button')
                        categoriasLista.append(elemento.text)
                    except:
                        categoriasLista.append(elemento.text)
                for elemento in nombres:
                    nombresLista.append(elemento.text)
                    print(f'{elemento.text} {len(nombresLista)}') #Este print es sólo para monitorear avance
                for elemento in primerosApellidos:
                    apellidos1.append(elemento.text)
                for elemento in segundosApellidos:
                    apellidos2.append(elemento.text)
                for elemento in edades:
                    edadesLista.append(elemento.text)
                for elemento in sexos:
                    sexosLista.append(elemento.text)
                for elemento in nacionalidades:
                    nacionalidadesLista.append(elemento.text)
                for elemento in fechas:
                    fechasLista.append(elemento.text)
                for elemento in autoridades:
                    autoridadesLista.append(elemento.text)
                for elemento in estados:
                    estadosLista.append(elemento.text)
            #Si por algún motivo no encuentra los datos a extraer, intentará nuevamente        
            except StaleElementReferenceException:
                break

        #Usamos esta condicionante para dar clic o no en el botón siguiente       
        if paginaActual < ultimaPagina:
            #Buscamos el botón siguiente
            btnSiguiente = driver.find_element(by='xpath', value='//a[@id="t-busq_next"]')
            #Intentamos dar clic con cualquiera de los dos métodos descritos
            try:
                btnSiguiente.click()
            except:
                driver.execute_script("arguments[0].click();", btnSiguiente)
            time.sleep(1) #Esperamos que cargue
        
        #Especificamos que ya estamos en la siguiente página, al momento que este valor sea mayor
        #que la última página, saldrá del bucle while, pues habrá terminado la extracción    
        paginaActual += 1 


    #Generamos una nueva lista para colocar los nombres completos de las personas desaparecidas
    nombresCompletos = []
    #Con un bucle for, iteraremos en cada valor de nombresLista, que tiene los nombres, pero no los apellidos
    for i, nombre in enumerate(nombresLista):
        try:
            nombreCompleto = f'{nombre} {apellidos1[i]} {apellidos2[i]}'
            print(nombreCompleto)
        except:
            nombreCompleto = "SIN INFORMACION"
        nombresCompletos.append(nombreCompleto)

    #Generaremos la base de datos final de la extracción por estado
    df = pd.DataFrame({"folio": foliosLista,
                    "categoria": categoriasLista,
                    "nombre": nombresLista,
                    "primer_apellido": apellidos1,
                    "segundo_apellido": apellidos2,
                    "nombre_completo": nombresCompletos,
                    "edad": edadesLista,
                    "sexo": sexosLista,
                    "nacionalidad": nacionalidadesLista,
                    "fecha_desaparicion": fechasLista,
                    "autoridad_reportante": autoridadesLista,
                    "estado": estadosLista})
    
    #La guardaremos en formato csv
    df.to_csv(f'cedulas/{entidad}/version_publica_federal_dic2023.csv', index=False)

#Al terminar el bucle for, es decir, al extraer los datos de todos los estados que necesitamos,
#cerramos el navegador
driver.quit()