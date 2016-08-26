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
from lxml import etree
hocr = etree.parse('orgambide.hocr.tmp')

def find_middle_line(page):
    page_width = int(page.get('title').split('; ')[1].split(' ')[3])
    left_margin = page_width
    right_margin = 0
    for line in page.xpath('.//*[@class="ocr_line"]'):
        line_x1 = int(line.get('title').split('; ')[0].split(' ')[1])
        line_x2 = int(line.get('title').split('; ')[0].split(' ')[3])
        if line_x1 < left_margin:
            left_margin = line_x1
        if line_x2 > right_margin:
            right_margin = line_x2
    middle = (right_margin - left_margin) / 2 + left_margin
    return middle

for page in hocr.xpath('//*[@class="ocr_page"]'):
    page_number = page.get('id').split('_')[1]
    middle_line = find_middle_line(page)
    # TENGO QUE VER CÓMO IGNORAR LÍNEAS CENTRADAS (CRUZAN LA MITAD)
    left_column = []
    right_column = []
    for line in page.xpath('.//*[@class="ocr_line"]'):
        line_x1 = int(line.get('title').split('; ')[0].split(' ')[1])
        if line_x1 < middle_line:
            left_column.append(line)
        elif line_x1 >= middle_line:
            right_column.append(line)
    print('Page %s' % page_number)
    print('Left column: %d lines' % len(left_column))
    print('Right column: %d lines' % len(right_column))


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
