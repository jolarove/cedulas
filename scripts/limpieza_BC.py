import pandas as pd
import re

datosBC = pd.read_csv('cedulas/BC_cedulas/datos_imagenes.csv')

nombres = []
estatus = []
for i, fila in datosBC.iterrows():
    descripcion = str(fila['Descripción'])
    nombre = re.findall(r'\b[A-ZÁÉÍÓÚÑÜ]+\b(?:\s+\b[A-ZÁÉÍÓÚÑÜ]+\b)+', descripcion)
    nombre = ' '.join(nombre) if nombre else 'SIN DATO'
    nombres.append(nombre)
    print(nombre)
datosBC['Nombre'] = nombres
datosBC.to_csv('cedulas/BC_cedulas/datos_imagenes.csv', index=False)

sinDato = datosBC['Nombre'].isin(['SIN DATO'])
cedulasBC = datosBC[~sinDato]
cedulasBC.to_csv('cedulas/BC_cedulas/datos_cedulas.csv', index=False)