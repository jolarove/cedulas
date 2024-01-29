from PIL import Image
import pytesseract

# Abre la imagen
image = Image.open('cedulas/imagenes/todas/Zadkiel Rafael Arévalo Galván Desaparecido_1054.png')

# Utiliza Tesseract para extraer texto
texto_imagen = pytesseract.image_to_string(image)

# Imprime el texto extraído
print(texto_imagen)

lineas = texto_imagen.split('\n')

# Inicializa variables para almacenar la información
nombre = ""
edad = ""
senas_particulares = ""
cabello = ""
tez = ""
complexion = ""
estatura = ""
vestimenta = ""
ultima_vez_visto = ""



# Recorre las líneas y busca la información deseada
for linea in lineas:
    if "Nombre:" in linea:
        nombre = linea.replace("Nombre:", "").strip()
    elif "Edad:" in linea:
        edad = linea.replace("Edad:", "").strip()
    elif "Sefias particulares:" in linea:
        senas_particulares = linea.replace("Sefias particulares:", "").strip()
    elif "Cabello:" in linea:
        cabello = linea.replace("Cabello:", "").strip()
    elif "Tez:" in linea:
        tez = linea.replace("Tez:", "").strip()
    elif "Complexién:" in linea:
        complexion = linea.replace("Complexién:", "").strip()
    elif "Estatura:" in linea:
        estatura = linea.replace("Estatura:", "").strip()
    elif "Vestimenta:" in linea:
        vestimenta = linea.replace("Vestimenta:", "").strip()
    elif "Sele vio por tiltima vez:" in linea:
        ultima_vez_visto = linea.replace("Sele vio por tiltima vez:", "").strip()

# Imprime la información extraída
print("Nombre:", nombre)
print("Edad:", edad)
print("Señas Particulares:", senas_particulares)
print("Cabello:", cabello)
print("Tez:", tez)
print("Complexión:", complexion)
print("Estatura:", estatura)
print("Vestimenta:", vestimenta)
print("Última vez visto:", ultima_vez_visto)
