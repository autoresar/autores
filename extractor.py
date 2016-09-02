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

autores = []
for page in hocr.xpath('//*[@class="ocr_page"]'):
    page_number = int(page.get('id').split('_')[1])
    # página 204 fue interpretada erróneamente por OCR como de una sola columna
    if page_number in [204,333]:
        continue
    col1_left, col1_right, col2_left, col2_right = getMargins(page)
    for line in page.xpath('.//*[@class="ocr_line"]'):
        line_x1 = int(line.get('title').split('; ')[0].split(' ')[1])
        line_x2 = int(line.get('title').split('; ')[0].split(' ')[3])
        #pdb.set_trace()
        if line_x2 <= col1_right:
            rel_indent = (line_x1 - col1_left) / (col1_right - col1_left)
        elif line_x1 >= col2_left:
            rel_indent = (line_x1 - col2_left) / (col2_right - col2_left)
        else:
            print(line)
            continue
        #pdb.set_trace()
        if rel_indent > .05 and rel_indent < .2:
        # podría dibujar un histograma para ver dónde ocurren las sangrías
            autores.append([line])
        else:
            autores[-1].append(line)

for autor in autores:
    print(autor[0].xpath('.//*[@class="ocrx_word"]//text()'))

# cuando la columna está torcida, las líneas más a la derecha de la línea más a la izquierda se interpretan como indentadas
# en la pág 397 del original hay una línea vertical que confunde al OCR
# Hay mucho texto indentado que no es nuevo párrafo. Hay que validar autor también antes de romper lista
# quizá debería cambiar estrategia e ir directamente por líneas que comienzan con alta concentración de mayúsculas


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
