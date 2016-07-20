#!/usr/bin/env python
"""integrador.py resultados volcado salida
Integra el resultado devuelto por autores.py con el último volcado
de la base.

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
import csv
import pdb
import re
import unicodedata
import Levenshtein
import sys

resultados = 'output/resultados.csv'
volcado = 'output/dbdump.csv'
importable = 'output/importame.csv'
if sys.argv[1]:
    resultados = sys.argv[1]
if sys.argv[2]:
    volcado = sys.argv[2]
if sys.argv[3]:
    importable = sys.argv[3]

class AutoVivification(dict):
    """Implementation of perl's autovivification feature.
    Crea claves no declaradas anteriormente en diccionarios anidados."""
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value


def simplificar(texto):
    """Convierte mayúsculas en minúsculas y simplifica caracteres especiales"""
    texto = texto.lower()
    texto = (unicodedata.normalize('NFD', texto).encode('ascii', 'ignore')
             .decode())
    return texto


def obtenerVariantes(nombre, apellido, genero):
    no_dividir = (r'de(?:\s+(?:la|las|los))?|del|'
                  'di|de(?:llo|lla|i|gli|lle)|'
                  'von|van(?:\s+(?:de|der|den)?)')
    primer_apellido = (r'(?P<primero>^(?:(?:%s)\s+)?\S*)' % no_dividir)
    # ignora conjunción "y" después del primer apellido; si es mujer, también
    # ignora preposición "de":
    if genero == 'Mujer':
        ultimos_apellidos = (r'\s+(?:y |de )?(?P<ultimos>.*)')
    else:
        ultimos_apellidos = (r'\s+(?:y )?(?P<ultimos>.*)')
    patron_apellido = (r'^%s(?:%s)?$' % (primer_apellido, ultimos_apellidos))
    apellido = re.match(patron_apellido, apellido, re.IGNORECASE)
    primer_nombre = r'(?P<primero>\S*)'
    # ignora "de", "de la", "de las" y "de los" iniciales del segundo nombre
    ultimos_nombres = r'\s+(?:de (?:la |las |los )?)?(?P<ultimos>.*)'
    patron_nombre = (r'^%s(?:%s)?$' % (primer_nombre, ultimos_nombres))
    nombre = re.match(patron_nombre, nombre, re.IGNORECASE)
    # para evitar duplicados, sólo nombre/apellido completo a la lista de
    # variantes de nombre/apellido si encontró más de un nombre/apellido:
    variantes_apellido = [apellido.group('primero'),
                          apellido.group('ultimos')]
    if apellido.group() != apellido.group('primero'):
        variantes_apellido.insert(0, apellido.group())
    variantes_nombre = [nombre.group('primero'), nombre.group('ultimos')]
    if nombre.group() != nombre.group('primero'):
        variantes_nombre.insert(0, nombre.group())
    variantes = []
    for variante_apellido in variantes_apellido:
        for variante_nombre in variantes_nombre:
            if not (variante_apellido is None or variante_nombre is None):
                variantes.append(variante_nombre + ' ' + variante_apellido)
    # remueve el primer elemento, ya que es la variante de nombre original:
    variantes.pop(0)
    return variantes


def abrirDump(filename):
    nids = {}
    autores = AutoVivification()
    with open(filename) as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=',', quotechar='"')
        campos = csvreader.fieldnames
        for linea in csvreader:
            # si años de nacimiento o de muerte no están disponibles, intenta
            # obtenerlos de las fechas de nacimiento o de muerte:
            if not linea['ano_nacimiento']:
                linea['ano_nacimiento'] = linea['fecha_nacimiento'][-4:]
            if not linea['ano_muerte']:
                linea['ano_muerte'] = linea['ano_muerte'][-4:]

            nid = linea['nid']
            nids[nid] = linea
            # se simplifican mayúsuclas y caracteres especiales:
            apellido = simplificar(linea['apellidos'])
            nombre = simplificar(linea['nombres'])
            variantes = simplificar(linea['variantes'])
            nombre_completo = '%s %s' % (nombre, apellido)
            genero = linea['genero']
            if linea['ano_nacimiento']:
                ano_nacimiento = linea['ano_nacimiento']
            else:
                ano_nacimiento = 'sin año de nacimiento'
            nombres = set([nombre_completo])
            nombres |= set(variantes.split('|'))
            nombres |= set(obtenerVariantes(nombre, apellido, genero))

            for nombre in nombres:
                autores[nombre][ano_nacimiento][nid] = nids[nid]
    return campos, nids, autores


def verConflictos(nuevo, viejo, ignorar_conflictos):
    """Busca conflictos entre 'nuevo' y 'viejo' en los campos enumerados en la
    variable 'foco' definida en esta función, y devuelve una lista de los
    conflictos identificados. Si la opción ignorar_conflictos está configurada,
    devuelve una versión de 'viejo' con los campos en conflicto sobreescritos.
    Si esta opción no está configurada, devuelve la versión de 'viejo' sin
    modificar."""
    conflictos = []
    # incluye apellidos y nombres en la detección de conflictos porque podría
    # haber diferencias en el uso de las mayúsculas (que son ignoradas en la
    # identifiación de duplicados)
    foco = ['apellidos', 'nombres', 'genero', 'lugar_nacimiento',
            'fecha_nacimiento', 'fecha_muerte', 'ano_muerte']
    for campo in foco:
        if campo in nuevo:
            campo_nuevo = nuevo[campo]
        else:
            campo_nuevo = ''
        campo_viejo = viejo[campo]
        if campo_nuevo and campo_viejo and campo_nuevo != campo_viejo:
            if ignorar_conflictos:
                viejo[campo] = campo_nuevo
            else:
                conflictos.append('%s: %s / %s' % (campo, campo_nuevo,
                                                   campo_viejo))
    if len(conflictos) == 0:
        conflictos = ['sin conflictos']
    return ', '.join(conflictos), viejo


def fusionarEnlaces(autor):
    fusion = []
    for i, titulo in enumerate(autor['enlaces_titulo'].split('|')):
        url = autor['enlaces_url'].split('|')[i]
        if titulo:
            fusion.append(titulo + '>>' + url)
    fusion = '|'.join(fusion)
    return fusion


def separarEnlaces(autor):
    titulos = []
    urls = []
    for enlace in autor['enlaces'].split('|'):
        titulos.append(enlace.split('>>')[0])
        if enlace:
            urls.append(enlace.split('>>')[1])
    titulos = '|'.join(titulos)
    urls = '|'.join(urls)
    del autor['enlaces']
    return titulos, urls


def hacerFinal(campos, linea, tipo, obs):
    """Transforma la línea al formato final"""
    final = {}
    for campo in campos:
        final[campo] = linea[campo]
    final['obs_tipo'] = tipo
    final['obs_descripcion'] = obs
    return final


def combinar(campos, nuevo, viejo, ignorar_conflictos):
    """Devuelve la combinación de nuevo y viejo en los campos indicados"""
    final = {}
    lista_campos = campos[:]
    conflictos, viejo = verConflictos(nuevo, viejo, ignorar_conflictos)
    if conflictos == 'sin conflictos':
        adiciones = []
        # fusiona los campos enlaces antes de combinar:
        lista_campos.remove('enlaces_titulo')
        lista_campos.remove('enlaces_url')
        lista_campos.append('enlaces')
        nuevo['enlaces'] = fusionarEnlaces(nuevo)
        viejo['enlaces'] = fusionarEnlaces(viejo)
        for campo in lista_campos:
            campo_nuevo = set()
            campo_viejo = set()
            if nuevo[campo]:
                campo_nuevo = set(nuevo[campo].split('|'))
            if viejo[campo]:
                campo_viejo = set(viejo[campo].split('|'))
            adicion = '|'.join(campo_nuevo - campo_viejo)
            if adicion:
                adiciones.append('%s: %s' % (campo, adicion))
            final[campo] = '|'.join(campo_nuevo | campo_viejo)
        if not adiciones:
            adiciones = ['sin adiciones']
        adiciones = ', '.join(adiciones)
        # separa el campo enlaces antes de devolver resultado final:
        final['enlaces_titulo'], final['enlaces_url'] = separarEnlaces(final)
        final['obs_tipo'] = 'ADICIONES'
        final['obs_descripcion'] = adiciones
    else:  # si hay conflictos
        conflictos = ('conflictos con %s %s (#%s): %s' % (viejo['nombres'],
                      viejo['apellidos'], viejo['nid'], conflictos))
        final = hacerFinal(campos, nuevo, 'CONFLICTOS', conflictos)
    return final


def escribirResultado(campos, autores):
    with open(importable, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, campos)
        writer.writeheader()
        for autor in autores:
            writer.writerow(autor)


def compararVariantes(autor, diccionario_variantes):
    """Devuelve un set de posibles duplicados precargados a partir de las
    variantes de nombre"""
    variantes = []
    if autor['variantes']:
        variantes += autor['variantes']
    nombre = autor['nombres']
    apellido = autor['apellidos']
    genero = autor['genero']
    variantes = obtenerVariantes(nombre, apellido, genero)
    posibles_autores = set()
    for variante in variantes:
        if variante in diccionario_variantes:
            variante = variante.lower()
            autores_encontrados = diccionario_variantes[variante]
            for autor in autores_encontrados:
                posibles_autores.add('%(nid)s: %(nombre)s (%(ano)s)' % autor)
    posibles_autores = ', '.join(posibles_autores)
    if not posibles_autores:
        posibles_autores = 'sin variantes'
    return posibles_autores


def buscarSimilares(cadena, diccionario, maxdist, ignorar_similares):
    """Buscar cadenas similares a la cadena entre las claves del diccionario,
    con distancias de edición de Levinshtein menor o iguales a maxdist"""
    if not ignorar_similares:
        nombres = diccionario.keys()
        mindist = maxdist
        nombres_similares = []
        for nombre in nombres:
            distancia = Levenshtein.distance(cadena, nombre)
            if distancia == mindist:
                nombres_similares.append(nombre)
            elif distancia < mindist:
                nombres_similares = [nombre]
                mindist = distancia
    similares = []
    for nombre in nombres_similares:
        for ano in diccionario[nombre]:
            for nid in diccionario[nombre][ano]:
                similar = diccionario[nombre][ano][nid]
                similares.append('%s %s (#%s)' % (similar['nombres'],
                                                  similar['apellidos'], nid))
    similares = ', '.join(similares)
    return similares


def obtenerOpciones(autor, lista_opciones):
    """Devuelve un tuple de unos y ceros para las opciones enumeradas en la
    lista, según cómo hayan sido configuradas para el autor."""
    valor_opciones = []
    for opcion in lista_opciones:
        if opcion in autor['opciones']:
            valor_opciones.append(1)
        else:
            valor_opciones.append(0)
    return tuple(valor_opciones)


def main():
    salida = []
    campos, dicc_nids, dicc_autores = abrirDump(volcado)
    with open(resultados) as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=',', quotechar="'")
        for linea in csvreader:
            # si el nombre de campo no existe, crea uno vacío
            for campo in campos:
                if not campo in linea:
                    linea[campo] = ''
            if not linea['ano_nacimiento']:
                linea['ano_nacimiento'] = linea['fecha_nacimiento'][-4:]
            if not linea['ano_muerte']:
                linea['ano_muerte'] = linea['ano_muerte'][-4:]
            # obtiene la configuración de las opciones:
            (forzar_nuevo,
             ignorar_conflictos,
             ignorar_similares) = obtenerOpciones(linea, ['forzar_nuevo',
                                                  'ignorar_conflictos',
                                                  'ignorar_similares'])
            apellido = simplificar(linea['apellidos'])
            nombre = simplificar(linea['nombres'])
            nombre_completo = '%s %s' % (nombre, apellido)
            ano_nacimiento = linea['ano_nacimiento']
            if forzar_nuevo:
                final = hacerFinal(campos, linea, 'NUEVO', 'forzado')
            elif nombre_completo in dicc_autores:
                if ano_nacimiento in dicc_autores[nombre_completo]:
                    viejos = dicc_autores[nombre_completo][ano_nacimiento]
                    if len(viejos) < 2:
                        viejo = list(viejos.values())[0]
                        final = combinar(campos, linea, viejo,
                                         ignorar_conflictos)
                    else:  # si más de un autor con mismo nombre y nacimiento
                        final = hacerFinal(campos, linea, '>1 AUTOR =NAC', '')
                else:  # si más de un autor con mismo nombre completo
                    otros_anos = ' / '.join(dicc_autores[nombre_completo]
                                            .keys())
                    final = hacerFinal(campos, linea, 'OTROS NAC', otros_anos)
            else:  # si no se encuentra autor con mismo nombre
                nombres_similares = buscarSimilares(nombre_completo,
                                                    dicc_autores, 2,
                                                    ignorar_similares)
                if nombres_similares:
                    final = hacerFinal(campos, linea, 'SIMILARES',
                                       nombres_similares)
                else:  # si no se encuentra un nombre similar
                    variantes = 'sin variantes'
                    if variantes != 'sin variantes':
                        final = hacerFinal(campos, linea, 'VARIANTES',
                                           variantes)
                    else:  # si no se encuentra nombre similar ni variante
                        final = hacerFinal(campos, linea, 'NUEVO',
                                           'sin observaciones')
            salida.append(final)
    campos += ['obs_tipo', 'obs_descripcion']
    pdb.set_trace()
    escribirResultado(campos, salida)

if __name__ == '__main__':
    main()
