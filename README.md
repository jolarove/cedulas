Obtención de Datos

Se emplearon diversas fuentes públicas de información relacionadas con el Registro Nacional de Personas Desaparecidas y No Localizadas (RNPDNO) en dos de sus versiones (agosto 2023 y julio 2024). Además, se utilizó web scraping para recopilar información de portales oficiales de seis entidades federativas de México con repositorios de cédulas de búsqueda en sus sitios de sus Comisiones Locales de Búsqueda.

Fuentes Principales

Registro Nacional de Personas Desaparecidas y No Localizadas (RNPDNO): Se descargaron mediante web scraping y analizaron las bases de datos disponibles en el portal oficial.

Portales de comisiones estatales de búsqueda: Se extrajo información directamente de las páginas oficiales de algunas comisiones estatales para complementar los datos nacionales.

Herramientas Utilizadas

Python: 
Librerías: requests, pandas, y selenium para la automatización del web scraping y el procesamiento de datos.

Google Sheets/Excel:

Para validación manual y visualización inicial de patrones y discrepancias (proceso realizado posterior a la extracción automatizada de datos, por lo que no está está disponible en este repositorio de GitHub).

Web Scraping

A continuación, se detalla el procedimiento:

Se seleccionaron portales públicos con información sobre personas desaparecidas, priorizando aquellos con datos actualizados y verificables.

Herramientas: Se utilizó Selenium para interactuar con portales dinámicos y extraer el contenido HTML.

Automatización: Los scripts fueron programados para navegar, identificar elementos relevantes y descargar los datos en formatos estructurados.
Limpieza de Datos:
Los datos extraídos fueron sometidos a un proceso de limpieza para eliminar duplicados, corregir errores de codificación (como caracteres especiales), normalizar formatos de fechas y ubicaciones.

Validación y Verificación:
Se realizó un proceso de verificación manual de las bases de datos extraídas para obtener la información que al final fue publicada en el reportaje “Desaparecidos: el engaño estadístico de México”.

Análisis de las Bases de Datos

Integración de Fuentes: 
Se combinaron las bases de datos obtenidas mediante scraping. Se identificaron inconsistencias como registros duplicados, datos incompletos o divergencias entre fuentes.

Procesamiento de Datos: 
Se utilizaron herramientas estadísticas para medir el impacto del subregistro.

Protección de Datos Sensibles:
Los datos recopilados fueron tratados con el máximo respeto a la privacidad de las personas desaparecidas y sus familias. No se publicaron detalles personales que pudieran poner en riesgo su integridad.

Transparencia:
El proceso de recolección, análisis y publicación de datos fue documentado minuciosamente para garantizar su reproducibilidad y verificar la metodología.

Limitaciones

Algunas plataformas restringen la cantidad de información accesible mediante scraping o imponen barreras técnicas. La falta de estandarización entre diferentes registros dificulta la integración completa de los datos.

Conclusión

El uso de bases de datos públicas y técnicas de web scraping permitió documentar las discrepancias y deficiencias en la gestión de información sobre personas desaparecidas en México. Esta metodología asegura un análisis objetivo y fundamentado, proporcionando evidencia para sustentar las conclusiones del reporte.
