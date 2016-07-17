#!/usr/bin/env python
"""integrador.py
Integra la información devuelta por autores.py con el último volcado
de la base en dbdumb.csv.

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


class AutoVivification(dict):
    """Implementation of perl's autovivification feature.
    Crea claves no declaradas anteriormente en diccionarios anidados."""
    def __getitem__(self, item):
        try:
            return dict.__getitem__(self, item)
        except KeyError:
            value = self[item] = type(self)()
            return value


def obtenerVariantes(nombre, apellido, genero):
    no_dividir = (r'de(?:\s(?:la|las|los))?|del|'
                  'di|de(?:llo|lla|i|gli|lle)|'
                  'von|van(?:\s(?:de|der|den)?)')
    primer_apellido = (r'(?P<primero>^(?:(?:%s)\s)?\S*)' % no_dividir)
    # ignora conjunción "y" después del primer apellido; si es mujer, también
    # ignora preposición "de":
    if genero == 'Mujer':
        ultimos_apellidos = (r'\s(?:y |de )?(?P<ultimos>.*$)')
    else:
        ultimos_apellidos = (r'\s(?:y )?(?P<ultimos>.*$)')
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
    arbol = AutoVivification()
    diccionario_variantes = {}
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

            apellido = linea['apellidos']
            nombre = linea['nombres']
            # los nombres completos se obtienen como "nombre apellido" porque
            # así es como están cargadas las variantes de nombre.
            nombre_completo = '%s %s' % (nombre, apellido)
            ano_nacimiento = linea['ano_nacimiento']
            if ano_nacimiento in arbol[nombre_completo.lower()]:
                arbol[nombre_completo.lower()][ano_nacimiento].append(linea)
            else:
                arbol[nombre_completo.lower()][ano_nacimiento] = [linea]
            # obtiene variantes del nombre y agrega info del autor al
            # diccionario de variantes:
            genero = linea['genero']
            variantes = set(linea['variantes'].split('|'))
            variantes |= set(obtenerVariantes(nombre, apellido, genero))
            for variante in variantes:
                variante = variante.lower()
                info_autor = {'nid': linea['nid'], 'nombre': nombre_completo,
                              'ano': ano_nacimiento}
                if variante in diccionario_variantes:
                    diccionario_variantes[variante].append(info_autor)
                elif variante:
                    diccionario_variantes[variante] = [info_autor]
    return campos, arbol, diccionario_variantes


def verConflictos(nuevo, viejo, ignorar_conflictos):
    conflictos = []
    foco = ['genero', 'lugar_nacimiento', 'fecha_nacimiento', 'fecha_muerte',
            'ano_muerte']
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


def obtenerFinal(campos, nuevo, viejo={}):
    if not viejo:
        viejo = nuevo
    final = {}
    adiciones = []
    for campo in campos:
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
    final['obs_tipo'] = 'ADICIONES'
    final['obs_descripcion'] = adiciones
    return final


def escribirResultado(campos, autores):
    with open('output/importame.csv', 'w') as csvfile:
        writer = csv.DictWriter(csvfile, campos)
        writer.writeheader()
        for autor in autores:
            writer.writerow(autor)


def compararVariantes(autor, diccionario_variantes):
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


def main():
    salida = []
    campos, dump, diccionario_variantes = abrirDump('output/dbdump.csv')
    with open('output/resultados.csv') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter=',', quotechar="'")
        for linea in csvreader:
            nuevo = linea
            viejo = None
            final = None
            # si el nombre de campo no existe, crea uno vacío
            for campo in campos:
                if not campo in linea:
                    linea[campo] = ''
            # para construir el diccionario de nombres, se pasan a minúsculas
            # para evitar que no coincidan por simple diferencia de mayúsculas/
            # minúsculas:
            apellido = linea['apellidos'].lower()
            nombre = linea['nombres'].lower()
            nombre_completo = '%s %s' % (nombre, apellido)
            ano_nacimiento = linea['ano_nacimiento']
            if nombre_completo in dump and not linea['forzar_nuevo']:
                if ano_nacimiento in dump[nombre_completo]:
                    autores_viejos = dump[nombre_completo][ano_nacimiento]
                    if len(autores_viejos) < 2:
                        viejo = autores_viejos[0]
                        conflictos, viejo = (verConflictos(nuevo, viejo,
                                             linea['ignorar_conflictos']))
                        if conflictos == 'sin conflictos':
                            final = obtenerFinal(campos, nuevo, viejo)
                        else:
                            final = obtenerFinal(campos, nuevo)
                            final['obs_tipo'] = 'CONFLICTOS'
                            final['obs_descripcion'] = conflictos
                    else:
                        final = obtenerFinal(campos, nuevo)
                        final['obs_tipo'] = '>1 AUTOR MISMO NACIMIENTO'
                        final['obs_descripcion'] = ''
                else:
                    otros_anos = ' / '.join(dump[nombre_completo].keys())
                    final = obtenerFinal(campos, nuevo)
                    final['obs_tipo'] = 'OTROS NACIMIENTOS'
                    final['obs_descripcion'] = otros_anos
            else:
                final = obtenerFinal(campos, nuevo)
                variantes = compararVariantes(nuevo, diccionario_variantes)
                if variantes != 'sin variantes' and not linea['forzar_nuevo']:
                    final['obs_tipo'] = 'VARIANTES'
                    final['obs_descripcion'] = variantes
                else:
                    final['obs_tipo'] = 'NUEVO'
                    final['obs_descripcion'] = 'sin observaciones'
            salida.append(final)
    campos += ['obs_tipo', 'obs_descripcion']
    escribirResultado(campos, salida)

if __name__ == '__main__':
    main()
