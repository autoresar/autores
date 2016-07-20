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
    """Convierte mayúsculas en minúsculas, simplifica caracteres especiales y
    sustituye múltiples espacios por uno solo"""
    texto = texto.lower()
    texto = (unicodedata.normalize('NFD', texto).encode('ascii', 'ignore')
             .decode())
    texto = re.sub(r'\s+', ' ', texto)
    return texto


def obtenerVariantes(nombre, apellido, genero):
    no_dividir = (r'de(?:\s(?:la|las|los))?|del|'
                  'di|de(?:llo|lla|i|gli|lle)|'
                  'von|van(?:\s(?:de|der|den)?)')
    primer_apellido = (r'(?P<primero>^(?:(?:%s)\s)?\S*)' % no_dividir)
    # ignora conjunción "y" después del primer apellido; si es mujer, también
    # ignora preposición "de":
    if genero == 'Mujer':
        ultimos_apellidos = (r'\s(?:y |de )?(?P<ultimos>.*)')
    else:
        ultimos_apellidos = (r'\s(?:y )?(?P<ultimos>.*)')
    patron_apellido = (r'^%s(?:%s)?$' % (primer_apellido, ultimos_apellidos))
    apellido = re.match(patron_apellido, apellido, re.IGNORECASE)
    primer_nombre = r'(?P<primero>\S*)'
    # ignora "de", "de la", "de las" y "de los" iniciales del segundo nombre
    ultimos_nombres = r'\s(?:de (?:la |las |los )?)?(?P<ultimos>.*)'
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


def buscarSimilares(cadena, diccionario, maxdist, omitir):
    """Buscar cadenas similares a la cadena entre las claves del diccionario,
    con distancias de edición de Levinshtein menor o iguales a maxdist"""
    nombres = diccionario.keys()
    nombres_similares = []
    for nombre in nombres:
        distancia = Levenshtein.distance(cadena, nombre)
        if distancia <= maxdist:
            nombres_similares.append(nombre)
    similares = []
    for nombre in nombres_similares:
        for ano in diccionario[nombre]:
            for nid in diccionario[nombre][ano]:
                if nid not in omitir:
                    similar = diccionario[nombre][ano][nid]
                    similares.append('%s %s (#%s)' % (similar['nombres'],
                                                      similar['apellidos'],
                                                      nid))
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


def conCoincidencia(campos, linea, diccionario):
    nombre_completo = simplificar('%s %s' % (linea['nombres'],
                                             linea['apellidos']))
    coincidencia = diccionario[nombre_completo]
    omitir = linea['omitir'].replace(' ', '').split(',')
    ignorar_conflictos = 'ignorar_conflictos' in linea['opciones']
    ano_nacimiento = linea['ano_nacimiento']
    for ano in list(coincidencia.keys()):
        for nid in list(coincidencia[ano].keys()):
            if nid in omitir:
                del coincidencia[ano][nid]
        if len(coincidencia[ano]) == 0:
            del coincidencia[ano]
    if coincidencia:
        if ano_nacimiento in coincidencia:
            viejos = coincidencia[ano_nacimiento]
            if len(viejos) == 1:
                viejo = list(viejos.values())[0]
                final = combinar(campos, linea, viejo, ignorar_conflictos)
            else:
                otros = []
                for viejo in viejos.values():
                    otros.append('%s %s (#%s)' % (viejo['nombres'],
                                                  viejo['apellidos'],
                                                  viejo['nid']))
                otros = ', '.join(otros)
                final = hacerFinal(campos, linea, '>1 AUTOR =NAC', otros)
        else:
            otros_anos = []
            for ano in coincidencia:
                otros = []
                for nid in coincidencia[ano]:
                    otro = coincidencia[ano][nid]
                    otros.append('%s %s (#%s)' % (otro['nombres'],
                                                  otro['apellidos'],
                                                  otro['nid']))
                otros = ano + ': ' + ', '.join(otros)
                otros_anos.append(otros)
            otros_anos = ', '.join(otros_anos)
            final = hacerFinal(campos, linea, 'OTROS NAC', otros_anos)
    else:
        final = sinCoincidencia(campos, linea, diccionario)
    return final


def sinCoincidencia(campos, linea, diccionario):
    nombre_completo = simplificar('%s %s' % (linea['nombres'],
                                             linea['apellidos']))
    omitir = linea['omitir'].replace(' ', '').split(',')
    nombres_similares = buscarSimilares(nombre_completo, diccionario, 2,
                                        omitir)
    if nombres_similares:
        final = hacerFinal(campos, linea, 'SIMILARES', nombres_similares)
    else:  # si no se encuentra un nombre similar
        variantes = 'sin variantes'
        if variantes != 'sin variantes':
            final = hacerFinal(campos, linea, 'VARIANTES', variantes)
        else:  # si no se encuentra nombre similar ni variante
            final = hacerFinal(campos, linea, 'NUEVO', 'sin observaciones')
    return final


def ordenados(primero, segundo):
    ordenados = 0
    primero_apellido = primero.split(', ')[0].replace(' ', '')
    primero_nombre = primero.split(', ')[1].replace(' ', '')
    segundo_apellido = segundo.split(', ')[0].replace(' ', '')
    segundo_nombre = segundo.split(', ')[1].replace(' ', '')
    if primero_apellido == segundo_apellido:
        if primero_nombre == min(primero_nombre, segundo_nombre):
            ordenados = 1
    else:
        if primero_apellido == min(primero_apellido, segundo_apellido):
            ordenados = 1
    return ordenados


def main():
    salida = []
    campos, dicc_nids, dicc_autores = abrirDump(volcado)
    with open(resultados) as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=',', quotechar="'")
        nombre_anterior = ', '
        for linea in csvreader:
            pendientes = []
            # si el nombre de campo no existe, crea uno vacío
            for campo in campos:
                if not campo in linea:
                    linea[campo] = ''
                inicio = linea[campo][:4]
                if inicio == 'OBS:' or inicio == 'ERR:':
                    pendientes.append(campo)
            pendientes = ', '.join(pendientes)
            if not linea['ano_nacimiento']:
                linea['ano_nacimiento'] = linea['fecha_nacimiento'][-4:]
            if not linea['ano_muerte']:
                linea['ano_muerte'] = linea['ano_muerte'][-4:]
            apellido = simplificar(linea['apellidos'])
            nombre = simplificar(linea['nombres'])
            nombre_completo = '%s %s' % (nombre, apellido)
            apellido_nombre = '%s, %s' % (apellido, nombre)
            ignorar_conflictos = 'ignorar_conflictos' in linea['opciones']
            ignorar_orden = 'ignorar_orden' in linea['opciones']
            nid = linea['nid']
            if pendientes:
                final = hacerFinal(campos, linea, 'REVISION PENDIENTE',
                                   pendientes)
            elif ((not ordenados(nombre_anterior, apellido_nombre) and
                   not ignorar_orden)):
                obs = '%s < %s' % (apellido_nombre, nombre_anterior)
                final = hacerFinal(campos, linea, 'REVISAR ORDEN', obs)
            elif nid:
                if nid == '0':
                    linea['nid'] = ''
                    final = hacerFinal(campos, linea, 'NUEVO', 'forzado')
                else:
                    viejo = dicc_nids[nid]
                    final = combinar(campos, linea, viejo, ignorar_conflictos)
            elif nombre_completo in dicc_autores:  # con coincidencias
                final = conCoincidencia(campos, linea, dicc_autores)
            else:  # sin coincidencias
                final = sinCoincidencia(campos, linea, dicc_autores)
            if not pendientes:
                nombre_anterior = apellido_nombre
            salida.append(final)
    campos += ['obs_tipo', 'obs_descripcion']
    escribirResultado(campos, salida)

if __name__ == '__main__':
    main()
