# Proyecto autores.ar

## Descripción

### autores.py
Extrae la información de autores del "Breve diccionario biográfico de
autores argentinos: desde 1940" en breve_diccionario.hocr.

Modo de uso:

    autores.py FUENTE RESULTADOS

FUENTE: archivo hocr devuelto por el motor OCR

RESULTADOS: nombre del archivo csv donde se escribirán los resultados

También usa la información en:

* nombres.csv: una lista de nombres del Registro Civil de la Ciudad de Buenos
  Aires, con sus respectivos géneros.
* disciplinas.csv: versión csv de disciplinas.ods, indica qué disciplinas y
  subdisciplinas corresponden a qué rasgos.
* lugares.csv: una lista de capitales, provincias y países usada para
  validación.

### integrador.py
Integra el resultado devuelto por autores.py con el último volcado de la base.

Modo de uso:

  	integrador.py RESULTADOS VOLCADO IMPORTABLE

RESULTADOS: archivo csv devuelto por autores.py

VOLCADO: volcado de la base obtenido en
         http://www.dominiopublico.org.ar/dbdump.csv

IMPORTABLE: nombre del archivo csv donde se escribirán los resultados

## Instalación
Descargar y extraer zip, o clonar con Git.

## Requerimientos
* Python3
* python-Levenshtein: se usa en integrador.py para hallar nombres similares.
