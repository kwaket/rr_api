import os

import ujson


class Region():
    """Класс определяющий регион по кадастровому номеру.

    Данные для определения региона по кадастровому номеру взяты здесь:
    https://rosreestr.ru/wps/portal/cc_ib_OpenData?param_infoblock_document_path=openData_region.htm

    Основной словарь (regions.json) содержит все регионы
    Дополнительный словарь (regions_map.json) содержит полные названия регионов
    и их сокращенные версии соответствующие названиям на сайте Росреестра.
    """

    def __init__(self):
        self.regions = ujson.load(
            open(os.path.join('utils', 'regions', 'regions.json')))
        self.regions_map = ujson.load(
            open(os.path.join('utils', 'regions', 'regions_map.json')))

    def get_region(self, cadnum: str) -> str:
        '''Возвращает название региона по кадастровому номеру.'''
        return str(self.regions[cadnum.split(':')[0]])

    def get_region_rr(self, cadnum: str) -> str:
        '''Возвращает название региона по кадастровому номеру.
        Название соответствует названию на сайте Росреестра
        '''
        region = self.get_region(cadnum)
        if region in self.regions_map.keys():
            region = self.regions_map[region]
        return region
