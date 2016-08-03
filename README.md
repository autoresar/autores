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

IMPORTABLE: nombre del archivo csv donde se escribirán los resultados de la lectura del dump de la base y la planilla RESULTADOS

### Trabajando con la planilla

El integrador devuelve la planilla con el IMPORTABLE. Con esta planilla vamos a trabajar evaluando la información que nos devolvió después de pasar el integrador, pero no vamos a trabajar editándola de manera directa ya que podríamos crear conflictos. Simplemente sirve para revisar. Todos los cambios se deben hacer sobre la planilla RESULTADOS. Una vez que finalizamos de hacer los cambios en la planilla RESULTADOS, volvemos a correr el integrador y revisamos la planilla IMPORTABLE tantas veces como sea necesario.

La planilla con el IMPORTABLE tiene dos tipos de campos que son a los que deberemos prestar atención: obs_tipo, obs_descripcion y validación. Hay ¿X? observaciones diferentes (obs_tipo):

ADICIONES
NUEVO
CONFLICTOS
REVISAR ORDEN
SIMILARES

La forma más práctica de trabajar con la planilla es ordenando a través de los filtros, parados en la columna obs_tipo colocamos "Filtro estándar" y organizamos según la observación que queramos analizar. Cada una de estas categorías indica:

ADICIONES: se agrega información nueva a un autor ya existente. Si vamos a la columna NID vamos a ver el número de identificación del nodo correspondiente en la base de datos. Al lado del campo "obs_descripcion" nos va a indicar qué es la información que está adicionando. Puede ser un enlace, una fuente, una subdisciplina, o varios de estos campos a la vez. 

NUEVO: se crea un nuevo autor/nodo.

CONFLICTOS: Los conflictos se tienen que resolver en la planilla RESULTADOS. Esta opción indica que hay algún tipo de conflicto con un autor ya existente, por ejemplo, que no coinciden en la fecha de nacimiento, fecha de muerte, lugar de nacimiento o nombre. En el caso de nombre y variantes de nombre, se debe modificar el nombre en la planilla de RESULTADOS si corresponde (es decir, si se trata efectivamente del mismo autor), optándose siempre por dejar el nombre completo. Si se trata de diferencias entre el nombre de casada y el nombre de soltera, se coloca el nombre de casada en el campo "Variantes de nombre".

Si se trata de un conflicto porque las fuentes bibliográficas difieren en la información sobre fecha de nacimiento/muerte o lugar de nacimiento, en ese caso, hay que trabajar con el campo Notas como se indica en la Rutina de ingreso de autores [¿agregaríamos el links acá?]. Colocamos la información disidente en el campo Notas y restablecemos en cada uno de los campos en conflicto el valor original que está tomando del autor previamente cargado. Así, supongamos que nuestra primera fuente "Historia" dice que Miguel Pérez nació en 1961 en San Juan y falleció en 1980, mientras que la fuente "Arte", de la cual extrajimos la nueva información, dice que Miguel Pérez nació en 1962 en San Luis y falleció en 1981. En este caso, el primer paso es verificar que efectivamente se trata de la misma persona y que no son personas diferentes. Si está confirmado que son la misma persona pero varían los datos biográficos, la forma de resolverlo es: 

1. agregar la información disidente en el campo Notas según lo especificado en la Rutina de Ingreso de Autores, tomando la fuente "Artes"
2. unificar la información acorde a nuestra primera fuente "Historia" (nació en 1961, en San Juan, y falleció en 1980) en la planilla RESULTADOS
3. si hay más de una nota, las notas deben separarse con el símbolo pipe (símbolo:|) sin dejar espacio entre las notas. Ejemplo {nota}{libro=409}{2}{1961}|{nota}{libro=409}{3}{San Juan}

REVISAR ORDEN: el programa lee los apellidos por orden alfabético para asegurarse de que no haya habido errores con el OCR. Cuando nos entrega esta opción en la columna, es porque el autor no está en el orden alfabético esperado. Así, por ejemplo, si lee que hay un "Cifler" antes de un "Ciesler", nos dirá que revisemos el orden. En ese caso, la forma de resolver el problema es:

1. Recurrir a la fuente bibliográfica original y confirmar que se haya tratado de un error de lectura del OCR. Corregir en la planilla RESULTADOS el apellido de manera tal que refleje la información de la fuente bibliográfica.

2. Si se trata de un problema de lectura del tipo "de Vedia" y "Verdecito", donde nos indica que revisemos el "de", lo que corresponde en este caso es confirmar que efectivamente el apellido se escribe "de Vedia" y no "Vedia". Si no hay ningún conflicto con el orden, lo que se pone es ignorar_orden en la planilla RESULTADOS, en la columna opciones, en la línea correspondiente a los dos autores que están generando conflictos (de Vedia y Verdecito en este caso).

SIMILARES: el programa lee strings de texto e identifica autores que pueden ser similares. Los similares son leídos a partir de su existencia previa en la base de datos, con lo cual, siempre vamos a tener un conflicto entre un nodo/autor ya existente y con un NID asignado y un nuevo autor. En este caso, hay que desambiguar y asegurarse que no sean la misma persona o que el nombre esté mal escrito. Por ejemplo: Susana Cella y Susana Cerda, donde Cella ya existe en la base de datos y Cerda no. En este caso, confirmamos que Cerda y Cella son dos personas diferentes, y tenemos que la planilla nos dice que existe una "Nora Glikman" y que es similar a  "Nora Glickman". Los pasos a seguir son:

1. Si se comprueba que Glickman y Glikman son la misma persona, se corrije el nombre donde corresponda (puede ser en la planilla RESULTADOS o en la base de datos).
2. Si se comprueba que Cella y Cerda son diferentes personas, en el campo "Omitir" de la planilla Resultados, en la línea correspondiente a Cerdá, que sería nuestro nuevo autor vamos a poner el NID del autor (Cella), que está leyendo como similar.

VALIDACIÓN

Esta columna nos indica cuando hay algún problema en la validación. Al igual que con la columna "obs_tipo", lo mejor es filtrarla para encontrar rápidamente los problemas. Los problemas que puede identificar son: 

1. encuentra un término que no respeta los términos de las taxonomías fijas (por ejemplo, en vez de decir San Juan, dice San Juan, Argentina), por lo que lo considera un término inválido. 
2. encuentra que hay un enlace que ya es similar a uno existente (porque quien revisó la planilla no tuvo en cuenta que un autor ya cargado tenía enlace en Wikipedia, por ejemplo). En ese caso, se remueve el enlace en la planilla RESULTADOS.

Una vez que se corrigen todos los datos, es necesario volver a pasar el comando integrador.py comparando el dump de la base de datos con la planilla RESULTADOS. Esto dará una nueva planilla IMPORTABLE, que deberemos volver a revisar tantas veces como sea necesario hasta que en la columna "obs_tipo" nos queden sólo las opciones ADICIONES y NUEVO y en la columna "validación" sólo nos quede "OK".

## Instalación
Descargar y extraer zip, o clonar con Git.

## Requerimientos
* Python3
* python-Levenshtein: se usa en integrador.py para hallar nombres similares.
