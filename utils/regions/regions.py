import os

import ujson


class Region():

    def __init__(self):
        self.regions = ujson.load(
            open(os.path.join('utils', 'regions', 'regions.json')))
        self.regions_map = ujson.load(
            open(os.path.join('utils', 'regions', 'regions_map.json')))

    def get_region(self, cadnum):
        '''Возвращает название региона по кадастровому номеру.'''
        return self.regions[cadnum.split(':')[0]]

    def get_region_rr(self, cadnum):
        '''Возвращает название региона по кадастровому номеру.
        Название соответствует названию на сайте Росреестра
        '''
        region = self.get_region(cadnum)
        if region in self.regions_map.keys():
            region = self.regions_map[region]
        return region
