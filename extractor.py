#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xxx.py

xxx

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
import pdb
from lxml import etree
from statistics import mean
hocr = etree.parse('orgambide.hocr.tmp')
page_offset = 16
# indent_ratio_span indica sangrías mínima y máxima de una línea para ser
# considerada sangría de primera línea, en unidades relativas de ancho de
# columna:
indent_ratio_span = (.05, .15)


def getMargins(page):
    """Devuelve los márgenes izquierdo (l) y derecho (r) de las columnas 1 y 2:
    l1 l2 r1 r2."""
    # class="ocr_page" ...
    # title='image "FILENAME"; bbox 0 0 WIDTH HEIGHT; ppageno X'
    line_spans = []
    for line in page.xpath('.//*[@class="ocr_line"]'):
        # class="ocr_line" ...
        # title="bbox X1 Y1 X2 Y2; baseline ? ?"
        line_x1 = int(line.get('title').split('; ')[0].split(' ')[1])
        line_x2 = int(line.get('title').split('; ')[0].split(' ')[3])
        line_spans.append((line_x1, line_x2))
    col1_left_margin = min([span[0] for span in line_spans])
    col2_right_margin = max([span[1] for span in line_spans])
    middle_line = (col2_right_margin - col1_left_margin) / 2 + col1_left_margin
    if int(page.get('id').split('_')[1]) == 204:
        pdb.set_trace()
    col1_right_margin = max([span[1] for span in line_spans
                             if span[1] < middle_line])
    col2_left_margin = min([span[0] for span in line_spans
                            if span[0] > middle_line])
    return (col1_left_margin, col1_right_margin,
            col2_left_margin, col2_right_margin)


def getColumns(page):
    lines = page.xpath('.//*[@class="ocr_line"]')
    columns = []
    # title='image "FILENAME"; bbox 0 0 WIDTH HEIGHT; ppageno X'
    last_y = int(page.get('title').split('; ')[1].split()[4])
    for line in lines:
        # title="bbox X1 Y1 X2 Y2; baseline SLOPE INTERSECT"
        line_y = int(line.get('title').split('; ')[0].split()[2])
        # ignores the line if it is against the top of the page:
        if line_y == 0:
            continue
        elif line_y > last_y:
            columns[-1].append(line)
        else:
            columns.append([line])
        last_y = line_y
    return columns


def findLeftMargin(column):
    """Dada una lista de líneas de texto pertenecientes a una misma columna,
    devuelve los parámetros b y a de la recta x = b * y + a que define el
    márgen izquierdo de la columna. Devuelve también la longitud de línea más
    frecuente en la columna."""
    line_lengths = {}
    for line in column:
        line_x1 = int(line.get('title').split('; ')[0].split()[1])
        line_x2 = int(line.get('title').split('; ')[0].split()[3])
        line_length = line_x2 - line_x1
        if line_length in line_lengths:
            line_lengths[line_length].append(line)
        else:
            line_lengths[line_length] = [line]
    # retrieves lines with most frequent lengths and picks the longest:
    most_freq_lengths = sorted(line_lengths,
                               key=lambda k: len(line_lengths[k]))[-3:]
    main_length = max(most_freq_lengths)
    # gets x,y coordinates for first and last lines of length = main_length:
    x1 = int(line_lengths[main_length][0]
             .get('title').split('; ')[0].split()[1])
    y1 = int(line_lengths[main_length][0]
             .get('title').split('; ')[0].split()[2])
    x2 = int(line_lengths[main_length][-1]
             .get('title').split('; ')[0].split()[1])
    y2 = int(line_lengths[main_length][-1]
             .get('title').split('; ')[0].split()[2])
    b = (x2 - x1) / (y2 - y1)
    a = x1 - b * y1
    return (b, a, main_length)

autores = []
pages = hocr.xpath('//*[@class="ocr_page"]')
anomalous_pages = []
for page in pages:
    page_number = int(page.get('id').split('_')[1]) + page_offset
    columns = getColumns(page)
    if len(columns) != 2:
        anomalous_pages.append((page_number, len(columns)))
        continue
    for column in columns:
        # x = by + a
        b, a, column_width = findLeftMargin(column)
        for line in column:
            line_x = int(line.get('title').split('; ')[0].split()[1])
            line_y = int(line.get('title').split('; ')[0].split()[2])
            left_margin = line_y * b + a
            indent = line_x - left_margin
            if ((indent > indent_ratio_span[0] * column_width and
                 indent < indent_ratio_span[1] * column_width)):
                print(' '.join(line.xpath('.//*[@class="ocrx_word"]//text()')))

print('%d pages were found with number of columns other than 2:' %
      len(anomalous_pages))
for page in anomalous_pages:
    print('page %s: %d columns' % (page))
#
#     # página 204 fue interpretada erróneamente por OCR como de una sola columna
#     if page_number in [204,333]:
#         continue
#     col1_left, col1_right, col2_left, col2_right = getMargins(page)
#     # PUEDO CALCULAR MÁRGENES EVALUANDO SÓLO LAS LÍNEAS MÁS LARGAS
#     for line in page.xpath('.//*[@class="ocr_line"]'):
#         line_x1 = int(line.get('title').split('; ')[0].split(' ')[1])
#         line_x2 = int(line.get('title').split('; ')[0].split(' ')[3])
#         #pdb.set_trace()
#         if line_x2 <= col1_right:
#             rel_indent = (line_x1 - col1_left) / (col1_right - col1_left)
#         elif line_x1 >= col2_left:
#             rel_indent = (line_x1 - col2_left) / (col2_right - col2_left)
#         else:
#             print(line)
#             continue
#         #pdb.set_trace()
#         words = line.xpath('.//*[@class="ocrx_word"]')
#         if rel_indent > .05 and rel_indent < .2:
#         # podría dibujar un histograma para ver dónde ocurren las sangrías
#             autores.append(words)
#         else:
#             autores[-1] += words
#
# for autor in autores:
#     # obtiene el texto de cada elemento word del autor y lo concatena
#     print(' '.join([word.xpath('.//text()')[0] for word in autor]))
#     # FALLA SI EL ELEMENTO PALABRA ESTÁ VAĆIO (VER "ENCOMIENDO MIS COSAS A SU PARA...")

# cuando la columna está torcida, las líneas más a la derecha de la línea más a la izquierda se interpretan como indentadas
# en la pág 397 del original hay una línea vertical que confunde al OCR
# Hay mucho texto indentado que no es nuevo párrafo. Hay que validar autor también antes de romper lista
# quizá debería cambiar estrategia e ir directamente por líneas que comienzan con alta concentración de mayúsculas
# devuelve texto en línea 8 de la página 1 sin la última palabra: \n
# ''.join(hocr.xpath('//*[@class="ocr_page"][1]//*[@class="ocr_line"]')[7].xpath('.//text()')[:-1])

# # elimina los espacios ENTRE tags:
# doc = etree.parse('orgambide.hocr', etree.XMLParser(remove_blank_text=True))
#
# # elimina el namespace de todos los tags, pero es muy lento:
# doc = etree.iterparse('orgambide.hocr')
# for _, element in doc:
#     element.tag = element.tag.split('}')[1]
#
# len(doc.getroot()[1])  # devuelve el número de páginas
# etree.iselement(doc.getroot())  # True
# doc.getroot()[1][0].keys()
# doc.getroot()[1][0].get('class')  # ocr_page
#
# etree.tostring(doc.getroot()[1][0], method='text', encoding='utf-8').decode()
# doc.getroot()[1][0].xpath('string()')  # las últimas dos líneas son equivalentes
# doc.getroot()[1][0].xpath('//text()')  # acomoda elementos de texto en una lista,
#                                        # por alguna razón explora todo el doc
#
# par = doc.getroot()[1][0][1][0]
# # para cada elemento en par (incluyendo par), devuelve atributo 'class' y texto:
# for element in par.iter():
#     print('%s: %s' % (element.get('class'), element.text)
# # idem exceptuando elemento par:
# for element in par.iterchildren():
#     print('%s: %s' % (element.get('class'), element.text)
# for element in par.iterfind():
#     print()
#
# # devuelve elementos con nombre "html" ignorando namespaces:
# doc.xpath('/*[local-name(.) = "html"]')
# # similar anterior:
# doc.xpath('//ns:html',namespaces={'ns':'http://www.w3.org/1999/xhtml'})
# doc.xpath('//ns:*[@class="ocr_page"]', namespaces = {'ns': 'http://www.w3.org/1999/xhtml'})
#
# # guarda todos los elementos @class='ocrx_word' de la primera página en
# # palabras y luego una por una extrae el texto de cada uno de ellos:
# palabras = doc.xpath('//ns:*[@class="ocr_page"][1]//*[@class="ocrx_word"]', namespaces = {'ns': 'http://www.w3.org/1999/xhtml'})
# for palabra in palabras:
#     print(palabra.text)
#
# # selecciona todas las líneas de la primera página:
# doc.xpath('//*[@class="ocr_page"]')[0].xpath('.//*[@class="ocr_line"]')
# # idem, usando axes:
# doc.xpath('//*[@class="ocr_page"]')[0].xpath('descendant::*[@class="ocr_line"]')
# doc.xpath('//*[@class="ocr_page"]')
#
# # devuelve el número de páginas (elementos con el atributo class=ocr_page), que
# # a su vez contienen elementos cuyo atributo id contiene "line_1_":
# len(doc.xpath('//*[@class="ocr_page"][.//*[contains(@id, "line_1_")]]'))
