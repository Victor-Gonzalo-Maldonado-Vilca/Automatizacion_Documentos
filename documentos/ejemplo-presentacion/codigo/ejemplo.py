from formatos import documentos_en

# Genera todos los documentos de una carpeta
for ruta, formato in documentos_en(carpeta):
    for archivo in formato.generar(ruta, salida, opciones):
        print(f"[{formato.NOMBRE}] {archivo.name}")
