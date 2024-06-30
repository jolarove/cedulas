"""
Usamos la paquetería pandas para limpiar y analizar los datos que previamente extragimos
La finalidad es encontrar cuántos casos de personas desaparecidas que tienen cédula de búsqueda vigente,
fueron borrados en la actualización de diciembre de la versión pública del Registro Nacional de Personas
Desaparecidas
"""

#PAQUETERÏAS
import pandas as pd
import logging

#FUNCIONES
def eliminarCaracteres(texto):
    """
    Elimina los acentos y puntos

    Parámetros:
    texto(str): texto al que se le borrarán los acentos y puntos

    Retorna:
    texto(str): texto sin acentos ni puntos
    """
    caracteresValidos = ['A','E','I','O','U','a','e','i','o','u','']
    caracteresInvalidos = ['Á','É','Í','Ó','Ú','á','é','í','ó','ú','.']
    for caracterInvalido, caracterValido in zip(caracteresInvalidos, caracteresValidos):
        if caracterInvalido in texto:
            texto = texto.replace(caracterInvalido, caracterValido)
    return texto

def eliminarEspacios(valores):
    """
    Elimina los espacios en blanco tanto al inicio, como al final y en medio de una cadena de texto

    Parámetros:
    valores(df): data frame donde están los textos a los que hay que eliminarles los espacios demás

    Retorna:
    columna(df): data frame con los valores sin espacios adicionales
    """
    columna = valores.str.strip().str.replace("  ", " ")
    return columna

def cruceDatos(df1, df2, columnas):
    """
    Cruza dos bases de datos y elimina duplicados

    Parámetros:
    df1(df) y df2(df): data frames a cruzar
    columnas(list): columnas que se utilizarán para encontrar coincidencias y cruzar

    Retorna:
    nuevoDf(df): nuevo data frame con el resultado del cruce de las bases de datos
    """
    nuevoDf = pd.merge(df1, df2, on=columnas, how='inner')
    nuevoDf = nuevoDf.drop_duplicates(subset=columnas)
    logger.info(f'En la base de datos hay: {len(nuevoDf)} desaparecidos con cédula')
    return nuevoDf

#ACCIONES

#Configuramos el logger para los mensajes
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

#Importamos las bases de datos de cada estado
datosEdoMex = pd.read_csv('cedulas/Datos/Estados/datos_cedulas_Estado de México.csv')
datosGuanajuato = pd.read_csv('cedulas/Datos/Estados/datos_cedulas_Guanajuato.csv')
datosJalisco = pd.read_csv('cedulas/Datos/Estados/datos_cedulas_Jalisco.csv')
datosPuebla = pd.read_csv('cedulas/Datos/Estados/datos_cedulas_Puebla.csv')
datosTabasco = pd.read_csv('cedulas/Datos/Estados/datos_cedulas_Tabasco.csv')
datosVeracruz = pd.read_csv('cedulas/Datos/Estados/datos_cedulas_Veracruz.csv')
logger.info('Bases de datos importadas con éxito')

#Creamos una lista con esas bases de datos
estados = [datosEdoMex, datosGuanajuato, datosJalisco, datosPuebla, datosTabasco, datosVeracruz]

#Con un bucle for eliminamos acentos y puntos en la columna nombre
for estado in estados:
    nombres = []
    for i, registro in estado.iterrows():
        nombre = str(registro['Nombre'])
        nombreFormato = eliminarCaracteres(nombre)
        nombres.append(nombreFormato)
    estado['Nombre'] = nombres
logger.info('Nombres correctamente formateados para eliminar acentos y puntos')

"""
En los estados que se necesite, filtraremos para encontrar los datos de personas desaparecidas únicamente
Aplica para: Puebla, Jalisco y Veracruz. El resto son datos sólo de personas que siguen desaparecidas.
"""
logger.info('Comienza proceso para filtrar datos de Puebla, Jalisco y Veracruz')
"""
En el caso de Puebla, para encontrar los nombres de las personas desaparecidas hay que eliminar los
duplicados, toda vez que si un nombre aparece dos veces significa que hay dos cédulas: desaparición y
localización y, por ende, la persona ya está localizada.
"""
duplicados = datosPuebla['Nombre'].duplicated(keep=False)
datosPueblaFiltro = datosPuebla[~duplicados]
logger.info('Datos de desaparecidos de Puebla filtrados con éxito')

#Filtramos en Jalisco
filtroDesaparecidosJalisco = datosJalisco['Estatus'] == 'PERSONA DESAPARECIDA'
datosJaliscoFiltro = datosJalisco[filtroDesaparecidosJalisco]
logger.info('Datos de desaparecidos de Jalisco filtrados con éxito')

#Filtramos Veracruz
filtroDesaparecidosVeracruz = datosVeracruz['Estatus'] == 'Desaparecido'
datosVeracruzFiltro = datosVeracruz[filtroDesaparecidosVeracruz]
logger.info('Datos de desaparecidos de Veracruz filtrados con éxito')

"""
Definimos los parámetros para un nuevo data frame donde concentraremos la información homologada de todos
los estados
"""
logger.info("Inicia proceso para crear un df con los datos de las cédulas de todos los estados analizados")
columnas = ['Nombre', 'Estado', 'Url']
#Lista donde enviaremos todos los df creados en el bucle for siguiente
dfEstados = []

#Creamos una lista para agregar el nombre del estado que corresponda a cada caso
nombresEstados = ['ESTADO DE MEXICO', 'GUANAJUATO', 'JALISCO', 'PUEBLA', 'TABASCO', 'VERACRUZ']
desaparecidosEstados = [datosEdoMex, datosGuanajuato, datosJaliscoFiltro, datosPueblaFiltro,
                        datosTabasco, datosVeracruzFiltro]
#Con un bucle for creamos los df que enviaremos a la lista dfEstados
for estado, nombre in zip(desaparecidosEstados, nombresEstados):
    df = pd.DataFrame({'Nombre': estado['Nombre'].to_list(),
                       'Estado': [nombre]*len(estado),
                       'Url': estado['Url'].to_list()})
    dfEstados.append(df)

#Concatenamos todos los df en uno sólo
datosEstados = pd.concat(dfEstados, ignore_index=True)

#Homologamos para que todo esté en mayúsculas en la columna nombre y eliminamos espacios demás
datosEstados['Nombre'] = datosEstados['Nombre'].str.upper()
datosEstados['Nombre'] = eliminarEspacios(datosEstados['Nombre'])
#Exportamos la base de datos en formato csv
datosEstados.to_csv('cedulas/Datos/cedulas_estados.csv', index=False)
logger.info('Base de datos creada con éxito')

#Importamos las bases de datos del registro nacional
vpDatosAgo = pd.read_csv("cedulas/Datos/VP RNPDNO al 22-08-2023.csv", encoding='latin1')
vpDatosDic = pd.read_csv("cedulas/Datos/version_publica_dic2023.csv")
logger.info('Bases de datos del RNPD importadas con éxito')

#Formateamos el df de agosto para convertir los nan en cadenas vacías
vpDatosAgo = vpDatosAgo.fillna("")

#El df de agosto tienen el nombre de la persona fragmentado, lo uniremos con un bucle for
nombres = []
for i, registro in vpDatosAgo.iterrows():
    nombre = registro['Nombre']
    apellido1 = registro['Primer Apellido']
    apellido2 = registro['Segundo Apellido']
    nombreCompleto = f'{nombre} {apellido1} {apellido2}'
    nombres.append(nombreCompleto)

vpDatosAgo['Nombre'] = nombres
logger.info('Nombres completos generados para el df de agosto')

#Eliminamos los espacios de más 
vpDatosAgo['Nombre'] = eliminarEspacios(vpDatosAgo['Nombre'])
vpDatosAgo['Entidad de desaparición'] = eliminarEspacios(vpDatosAgo['Entidad de desaparición'])

#Renombramos las columnas para homologar encabezados
vpDatosDic.rename(columns={'Nombre completo': 'Nombre'}, inplace=True)
vpDatosAgo.rename(columns={'Entidad de desaparición': 'Estado'}, inplace=True)

logger.info('Iniciamos cruce de bases de datos')
#Cruzamos las bases de datos de agosto y diciembre con la de las cédulas de los estados
columnas = ['Nombre', 'Estado']
cedulasVpAgo = cruceDatos(vpDatosAgo, datosEstados, columnas)
cedulasVpDic = cruceDatos(vpDatosDic, datosEstados, columnas)

#Hacemos un cruce adicional para encontrar los registros borrados
cedulasRegistro = pd.merge(cedulasVpAgo, cedulasVpDic, on=['Nombre', 'Estado'], how='outer', indicator=True)
desaparecidosBorrados = cedulasRegistro[cedulasRegistro['_merge'] == 'left_only']
#Eliminamos las columnas que no necesitaremos
columnasDrop = ['Consecutivo Reportes por Persona', 'Consecutivo Registro', 'Primer Apellido',
                'Segundo Apellido', 'Edad_y', 'Sexo_y', 'Nacionalidad_y', 'Fecha desaparición', 
                'Autoridad', 'Url_y', '_merge']
desaparecidosBorrados = desaparecidosBorrados.drop(columns=columnasDrop)

#Renombramos las columnas que necesitamos y tienen nombres incorrectos
desaparecidosBorrados = desaparecidosBorrados.rename(columns={'Edad_x': 'Edad', 'Sexo_x': 'Sexo', 
                                                              'Nacionalidad_x': 'Nacionalidad', 'Url_x':'Url'})
#Exportamos en nuevo df en formato csv
desaparecidosBorrados.to_csv('cedulas/Datos/desaparecidos_borrados.csv', index=False)
logger.info(f'El gobierno de México borró al menos {len(desaparecidosBorrados)}')
logger.info('Proceso finalizado con éxito')
