#!/usr/bin/env python
"""autores.py

Extrae la información de autores del "Breve diccionario biográfico de
autores argentinos: desde 1940" en breve_diccionario.hocr.

Copyright (C) 2016 Proyecto autores.ar

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import re
import sys
import pdb
import difflib
import csv
import unicodedata

__author__ = ""
__copyright__ = "Copyright 2016, Proyecto autores.ar"
__credits__ = [""]
__license__ = "GPL"
__version__ = "3.0"
__maintainer__ = ""
__email__ = ""
__status__ = "Development"

primera_pagina = 17
discip_predet = 'Escritura'  # establece la disciplina predeterminada de la referencia

f = open('breve_diccionario.hocr', 'rU')
hocr = f.read()
f.close()

# cada clave de 'rasgos' es uno de los rasgos separados por comas obtenidos de
# la primera oración de la biografía del autor, y que fueron volcados al archivo
# 'disciplinas.csv'. El valor de cada uno de estos rasgos es una lista de
# disciplinas y subdisciplinas que le corresponden.
rasgos = {}
with open('disciplinas.csv') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    discip_opc = next(csvreader)[2:-1]
    for linea in csvreader:
        rasgos[linea[0]] = []
        for num, opcion in enumerate(linea[2:-1]):
            if int(opcion):
                rasgos[linea[0]].append(discip_opc[num])

def transformarRasgo(rasgo):
    """Transforma los rasgos obtenidos de la primera oración de la biografía
    del autor pasando todo a minúscula y unificando por género."""
    rasgo = rasgo.lower()
    # siguiendo las reglas en http://lema.rae.es/dpd/srv/search?id=Tr5x8MFOuD6DVTlDBg,
    # unifica la primera palabra de la disciplina a un único género
    rasgo = re.sub(r'^(\w*\s\w*)o\b', '\g<1>a', rasgo)  # todas las segundas palabras terminadas en "o" se suponen adjetivos masculinos y se pasan a femenino
    rasgo = re.sub(r'^(\w*)o\b', '\g<1>a', rasgo)  # todas las primeras palabras terminadas en "o" se suponen sustantivos masculinos y se pasan a femenino
    rasgo = re.sub(r'^(\w*)(ora|riz)\b', '\g<1>or', rasgo)  # todas las primeras palabras terminadas en "ora" o en "riz" se suponen sustantivos femeninos y se pasan a masculino
    rasgo = re.sub(r'^(\w*or\s\w*)a\b', '\g<1>o', rasgo)  # todas las segundas palabras terminadas en "a" precedidas por palabras terminadas en "or", se suponen adjetivos femeninos y se pasan a masculino
    return rasgo


def obtenerDisciplinas(lista_rasgos, disciplina_predeterminada):
    """A partir de una lista de rasgos, devuelve una cadena separada por barras
    verticales de disciplinas y una de subdisciplinas"""
    obs = 0  # indicador de observado; se enciende cuando un rasgo no tiene disciplinas asociadas
    empty = 0  # indicador de vacío; se enciende cuando ninguno de los rasgos tiene disciplinas asociadas
    mi_lista = []  # lista de disciplinas y subdisciplinas
    mis_disciplinas = set()
    mis_subdiscip = set()
    for rasgo in lista_rasgos:
        rasgo = transformarRasgo(rasgo)
        tmp = rasgos[rasgo]  # este paso traduce el rasgo en disciplina/subdisciplina
        mi_lista += tmp
    mi_lista = set(mi_lista)
    if 'REVISAR' in mi_lista:
        mi_lista.remove('REVISAR')
        obs = 1
    for elemento in mi_lista:
        mis_disciplinas.add(elemento.split(': ')[0])
        if elemento.split(': ')[1]:
            mis_subdiscip.add(elemento)
    if not mi_lista:
        empty = 1
    mis_disciplinas.add(disciplina_predeterminada)
    mis_disciplinas = '|'.join(mis_disciplinas)
    mis_subdiscip = '|'.join(mis_subdiscip)
    if not mis_disciplinas:
        mis_disciplinas = 'ERR: sin disciplinas asociadas'
    elif empty:
        mis_disciplinas = 'DEF: ' + mis_disciplinas
    elif obs:
        mis_disciplinas = 'OBS: ' + mis_disciplinas
    return (mis_disciplinas, mis_subdiscip)


def confianzaMinima(posicion_inicial, posicion_final, diccionario_confianza):
    """Devuelve la confianza media de las palabras en el rango dado por
    posicion_inicial : posicion_final."""
    lista_posiciones = sorted(diccionario_confianza.keys())
    if not posicion_inicial in lista_posiciones:
        posicion_inicial = [p for p in lista_posiciones if p < posicion_inicial][-1]
    indice_posicion_inicial = lista_posiciones.index(posicion_inicial)
    valores_confianza = []
    for posicion in lista_posiciones[indice_posicion_inicial:]:
        if not posicion > posicion_final:
            valores_confianza.append(diccionario_confianza[posicion])
    confianza_minima = min(valores_confianza)
    return confianza_minima


def validar_lugar(sitio, provincias, capitales, paises):
    if sitio == 'Buenos Aires': sitio = 'Capital Federal'  # si el texto identificado como provincia es sólo 'Buenos Aires', lo cambia por CABA
    sitio = re.sub(r'^Provincia\s*De\s*', '', sitio, flags=re.IGNORECASE)  # elimina fragmento 'Provincia de ' al principio del texto identificado como provincia
    umbral = .8
    if difflib.get_close_matches(sitio, provincias.keys(), n=1, cutoff=umbral):
        provincia = difflib.get_close_matches(sitio, provincias.keys(), n=1, cutoff=umbral)[0]
        sitio_valido = provincias[provincia]
    elif difflib.get_close_matches(sitio, capitales.keys(), n=1, cutoff=umbral):
        capital = difflib.get_close_matches(sitio, capitales.keys(), n=1, cutoff=umbral)[0]
        sitio_valido = capitales[capital]
    elif difflib.get_close_matches(sitio, paises.keys(), n=1, cutoff=umbral):
        pais = difflib.get_close_matches(sitio, paises.keys(), n=1, cutoff=umbral)[0]
        sitio_valido = paises[pais]
    else:
        sitio_valido = 'OBS: ' + sitio
    return sitio_valido

blocks = []
lheight = []
bdist = []

pages = re.finditer(r"<div class='ocr_page' id='page_(?P<id>\d*)'.*?bbox \d* \d* (?P<x2>\d*).*?>\s*(?P<content><div class='ocr_carea'.*?<\/div>\s*)<\/div>", hocr, re.DOTALL)

for page in pages:
    careas = re.finditer(r"<div class='ocr_carea' id='block_\d*_(?P<id>\d*)'.*?bbox (?P<x1>\d*) (?P<y1>\d*) (?P<x2>\d*).*?>\s*(?P<content>.*?)<\/div>", page.group('content'), re.DOTALL)
    first = {'col_1': 1, 'col_2': 1}

    for carea in careas:
        if 'linebase' in locals(): del linebase
        pars = re.finditer(r"<p class='ocr_par'.*?id='(?P<id>.*?)'.*?>(?P<content>.*?)<\/p>", carea.group('content'), re.DOTALL)
        btext = []
        pos = 0
        conf = {}
        pcount = 0
        opened = 1

        for par in pars:
            lines = re.finditer(r"<span class='ocr_line'.*?bbox \d* (?P<y1>\d*) (?P<x2>\d*) (?P<y2>\d*).*?(?P<baseline>-?\d*)\">\s*(?P<content><span class='ocrx_word'.*?<\/span>\s*)<\/span>", par.group('content'))
            ptext = []

            for line in lines:
                words = re.finditer(r"<span class='ocrx_word'.*?x_wconf (?P<conf>\d*).*?>(?:<\S*?>)*(?P<content>\S+?)(?:<\/\S*?>)*<\/span>", line.group('content'))
                ltext = []

                for word in words:
                    ltext.append(word.group('content'))
                    conf[pos] = int(word.group('conf'))
                    pos += len(word.group('content')) + 1

                if len(ltext):
                    ptext.append(' '.join(ltext))
                    # if 'linebase' in locals():
                    #     tmp = sum(lheight)/len(lheight)
                    #     if int(line.group('y1')) - linebase < tmp: print(ptext)
                    linebase = int(line.group('y2')) + int(line.group('baseline'))  # sumo baseline en vez de restarla porque la variable incluye el signo
                    lheight.append(linebase - int(line.group('y1')))

            if len(ptext):
                btext.append('\n'.join(ptext))

            pos += 1  # incrementa el marcador de posición en una unidad para compensar el doble salto de línea al final del párrafo
            pcount += 1

        conf[pos - 1] = None  # disminuye el marcador de posición en una unidad para compensar el doble salto de línea al final del bloque y guarda un último elemento vacío en conf
        blockWidth = int(carea.group('x2')) - int(carea.group('x1'))
        lastLineWidth = int(line.group('x2')) - int(carea.group('x1'))
        if (lastLineWidth < .95 * blockWidth): opened = 0

        if len(btext):
            if int(carea.group('x1')) < int(page.group('x2')) / 3:
                if first['col_1']: first['col_1'] = 0; continue  # ignora el bloque si es el primero de la columna
                blocks.append({'page': int(page.group('id')), 'col': 1, 'block': int(carea.group('id')),
                              'text': '\n\n'.join(btext), 'conf': conf, 'pcount': pcount,
                              'y1': int(carea.group('y1')), 'x1': int(carea.group('x1')), 'x2': int(carea.group('x2')),
                              'lastLineX2': int(line.group('x2')), 'lastLineY2': int(line.group('y2')) + int(line.group('baseline')), 'opened': opened})
            else:
                if first['col_2']: first['col_2'] = 0; continue
                blocks.append({'page': int(page.group('id')), 'col': 2, 'block': int(carea.group('id')),
                              'text': '\n\n'.join(btext), 'conf': conf, 'pcount': pcount,
                              'y1': int(carea.group('y1')), 'x1': int(carea.group('x1')), 'x2': int(carea.group('x2')),
                              'lastLineX2': int(line.group('x2')), 'lastLineY2': int(line.group('y2')) + int(line.group('baseline')), 'opened': opened})

blocks = sorted(blocks, key=lambda b: (b['page'], b['col'], b['block']))
lheight = sum(lheight)/len(lheight)

# junta dos bloques de una misma columna si la distancia entre ellos es menor
# que la mitad de la altura promedio de una línea de texto.
blocknum = 1
while blocknum < len(blocks):
    block = blocks[blocknum]
    prevblock = blocks[blocknum - 1]
    if (block['col'] == prevblock['col'] and
            block['y1'] - prevblock['lastLineY2'] < lheight):
        prevblock['text'] += '\n\n' + block['text']
        prevblock['pcount'] += 1  # incrementa el número de párrafos del bloque
        prevblock['lastLineY2'] = block['lastLineY2']
        prevblock['lastLineX2'] = block['lastLineX2']
        prevblock['x1'] = min(prevblock['x1'], block['x1'])
        prevblock['x2'] = max(prevblock['x2'], block['x2'])
        blockWidth = prevblock['x2'] - prevblock['x1']
        lastLineWidth = prevblock['lastLineX2'] - prevblock['x1']
        # reevalúa si se puede decir que el bloque está cerrado
        prevblock['opened'] = 1
        if (lastLineWidth < .95 * blockWidth): prevblock['opened'] = 0
        pos = max(prevblock['conf'].keys())
        for key in block['conf'].keys():
            prevblock['conf'][pos + key] = block['conf'][key]
        del blocks[blocknum]
    else:
        blocknum += 1

blocknum = 1
while blocknum < len(blocks):
    block = blocks[blocknum]
    prevblock = blocks[blocknum - 1]
    if prevblock['opened'] and block['col'] != prevblock['col']:
        match = re.match(r'^(.*?),', block['text'])
        if match:
            candidate = match.group(1)
            ratio = sum(1 for char in candidate if char.isupper()) / len(candidate)
            if ratio > .75: blocknum +=1; continue
        prevblock['text'] += '\n\n' + block['text']
        prevblock['pcount'] += 1
        prevblock['lastLineY2'] = block['lastLineY2']
        prevblock['lastLineX2'] = block['lastLineX2']
        prevblock['x1'] = min(prevblock['x1'], block['x1'])
        prevblock['x2'] = max(prevblock['x2'], block['x2'])
        blockWidth = prevblock['x2'] - prevblock['x1']
        lastLineWidth = prevblock['lastLineX2'] - prevblock['x1']
        prevblock['opened'] = 1
        if (lastLineWidth < .95 * blockWidth): prevblock['opened'] = 0
        pos = max(prevblock['conf'].keys())
        for key in block['conf'].keys():
            prevblock['conf'][pos + key] = block['conf'][key]
        del blocks[blocknum]
    else:
        blocknum += 1

# for num, block in enumerate(blocks):
#     match = re.search(r"^(.*?)\n{1,2}(?:\((.*?)\).*?\n{1,2})?\(([\s\S]*?)\)[\s\S]+\n\n(.*?)\n{1,2}(?:\((.*?)\)\s{0,2}\n{1,2})?\(([\s\S]*?)\)\s{0,2}\n{1,2}", block['text'])
#     if match: print(num)

# crea listas de capitales, provincias y países con información de lugares.csv
capitales = {}
provincias = {}
paises = {}
with open('lugares.csv') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    next(csvreader)  # ignora la primera línea del archivo csv
    for row in csvreader:
        if row[0] and not row[0] in capitales:
            capitales[row[0]] = row[1]  # + ', ' + row[2]  # quitar comentario para agregar país a continuación de la provincia
        if row[1] and not row[1] in provincias:
            provincias[row[1]] = row[1] # + ', ' + row[2]  # quitar comentario para agregar país a continuación de la provincia
        if row[2] and not row[2] in paises:
            paises[row[2]] = row[2]

# guarda lista de nombres y géneros del registro civil de la Ciudad de Buenos
# Aires en el diccionario "names"
names = {}
with open('nombres.csv') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for row in csvreader:
        names[unicodedata.normalize('NFD', row[0]).encode('ascii', 'ignore')] = row[1]

result = []
todos_los_rasgos = []

for blocknum, block in enumerate(blocks):
    (pagina, name, nick, lastname, name_conf, nick_conf, lastname_conf, gender,
     bplace, bprovincia, byear, dyear, byear_conf, dyear_conf,
     oracion, discip, subdiscip) = ('',) * 17
    pagina = block['page'] + primera_pagina - 1
    # bloque if que corrige páginas ausentes 68 y 69 de la digitalización original
    if pagina > 67:
        pagina += 2
    match = re.search(r"^(?P<name>.*?)\n{1,2}(?:\((?P<other>.*?)\).*?\n{1,2})?\((?P<data>[\s\S]*?)\).*?\n{1,2}(?P<oracion>[\s\S]*?)\.", block['text'])
    if match:
        # establece la posición aproximada en el bloque de texto de las variables de interés (para obtener los valores de confianza)
        name_pos = match.start('name')
        lastname_pos = match.start('name')
        byear_pos = match.start('data')
        dyear_pos = match.start('data')

        oracion = match.group('oracion')
        oracion = re.sub(r'[-|—]\n', '', oracion)
        oracion = re.sub(r'\n', ' ', oracion)
        oracion = re.sub(r'^es ', '', oracion, flags=re.IGNORECASE)
        mis_rasgos = re.split(r'(?:,\s?(?:[ye]\s)?|\s[ye]\s)', oracion)
        discip, subdiscip = obtenerDisciplinas(mis_rasgos, discip_predet)
        todos_los_rasgos += mis_rasgos  # esta línea es parte del código que arma la lista de rasgos encontrados en la fuente
        if match.group('other'):
            nick_pos = match.span('name')
            nick_conf = confianzaMinima(nick_pos[0], nick_pos[1], block['conf'])
            nick = match.group('name').title()
            fullname = match.group('other')
            name_pos = match.start('other')
        else:
            fullname = match.group('name')
        matchname = re.search(r"^(?P<lastname>.*?)\s?,\s*(?P<name>.*?)\s?$", fullname)
        if matchname:
            name_pos = tuple([i + name_pos for i in matchname.span('name')])
            lastname_pos = tuple([i + lastname_pos for i in matchname.span('lastname')])
            name_conf = confianzaMinima(name_pos[0], name_pos[1], block['conf'])
            lastname_conf = confianzaMinima(lastname_pos[0], lastname_pos[1], block['conf'])
            lastname = matchname.group('lastname').title()
            if not re.search(r"^(?:[^\W\d_]+(?:(?:\.? )|['-]))*[^\W\d_]+\.?$", lastname):  # este bloque if alerta si la parte del texto identificada como apellido tiene un formato distinto al esperado
                lastname = 'OBS: ' + lastname
            name = matchname.group('name').title()  # este bloque if alerta si la parte del texto identificada como nombre sigue un formato distinto al esperado
            if re.search(r"^(?:[^\W\d_]+(?:(?:\.? )|['-]))*[^\W\d_]+\.?$", name):
                firstname = unicodedata.normalize('NFD', name.split(' ')[0]).encode('ascii', 'ignore')
                if firstname in names:
                    gender = names[firstname]
                    if firstname == b'Maria': gender = 'Mujer'
                else:
                    gender = '?'
            else:
                name = 'OBS: ' + name
        else:
            name = 'ERR: ' + fullname
        matchdata = re.search(r"^(?P<bplace>[\s\S]*?),\s*(?P<byear>(?=(?:.{0,3}\d){3})\S{4})\s*(?:\s*[-|—]*\s*(?:(?P<dplace>[\s\S]*?),\s*)?(?P<dyear>(?=(?:.{0,3}\d){3})\S{4})\s*)?$", match.group('data'))
        if matchdata:
            byear_pos = tuple([i + byear_pos for i in matchdata.span('byear')])
            dyear_pos = tuple([i + dyear_pos for i in matchdata.span('dyear')])
            byear_conf = confianzaMinima(byear_pos[0], byear_pos[1], block['conf'])
            bplace = matchdata.group('bplace').replace('\n', ' ').title()
            bprovincia = re.search(r'^.*?(?:,\s?)?(?P<provincia>[^,]*)$', bplace).group('provincia')
            bprovincia = validar_lugar(bprovincia, provincias, capitales, paises)
            byear = matchdata.group('byear')
            if not re.search(r'\d{4}', byear):  # este bloque if alerta si la parte reconocida como año de nacimiento no sigue el formato esperado
                byear = 'OBS: ' + byear
            if matchdata.group('dplace'):
                dplace = matchdata.group('dplace').replace('\n', ' ').title()
                dprovincia = re.search(r'^.*?(?:,\s?)?(?P<provincia>[^,]*)$', dplace).group('provincia')
                dprovincia = validar_lugar(dprovincia, provincias, capitales, paises)
            if matchdata.group('dyear'):
                dyear_conf = confianzaMinima(dyear_pos[0], dyear_pos[1], block['conf'])
                dyear = matchdata.group('dyear')
                if not re.search(r'\d{4}', dyear):  # este bloque if alerta si la parte reconocida como año de muerte no sigue el formato esperado
                    dyear = 'OBS: ' + dyear
        else:
            bplace = 'ERR: ' + match.group('data')
    else:
        name = 'ERR: ' + block['text'].replace('\n', ' ')
    result.append((pagina, name, nick, lastname, gender, name_conf, nick_conf, lastname_conf,
                   bplace, bprovincia, byear, dyear, byear_conf, dyear_conf,
                   oracion, discip, subdiscip))

f = open('output/resultados.csv', 'w')
f.write("'página','nombres','seudonimos','apellidos','genero','name_conf','nick_conf','lastname_conf',"
        "'bplace','lugar_nacimiento','ano_nacimiento','ano_muerte','byear_conf','dyear_conf',"
        "'primera_oración','disciplinas','subdisciplinas',"
        "'notas','ignorar_conflictos','forzar_nuevo'\n")
for author in result:
    line = "'%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s',,," % author
    f.write(line+'\n')
f.close()

disciplinas = {}  # colección de disciplinas y número de veces que aparece cada una
for elemento in todos_los_rasgos:
    disciplina = transformarRasgo(elemento)
    if not disciplina in disciplinas:
        disciplinas[disciplina] = 1
    else:
        disciplinas[disciplina] += 1
