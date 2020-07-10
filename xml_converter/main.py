import os
import re
import contextlib

import requests
import lxml.etree as ET


def _add_to_downloaded(filepath):
    with open('downloaded.txt', 'a') as w:
        w.write(filepath + '\n')


def _is_downloaded(filepath):
    with contextlib.suppress(FileNotFoundError):
        return filepath in set(open('downloaded.txt').read().split('\n'))
    return False


def download_file(url, filepath):
    # local_filename = url.split('/')[-1]
    print(url, filepath)
    local_filename = filepath
    # NOTE the stream=True parameter belo  w
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                #if chunk:
                f.write(chunk)
    return local_filename


def _get_xsl_filename(xml_filename):
    with open(xml_filename) as afile:
        for line in afile.readlines():
            if line.startswith('<?xml-stylesheet'):
                url = re.findall(r'href="(.*)"', line)[0]
                filepath = url.split('rosreestr.ru/')[-1]
                if _is_downloaded(url):
                    return filepath
                _make_dirs_tree(os.path.split(filepath)[0] + '/')
                download_file(url, filepath)
                _add_to_downloaded(url)
                return filepath
    return None


def download_dependencies(xsl_filename):
    afile = open(xsl_filename)
    pattern = r'\<xsl\:variable\b.*select\="document\(\'(.*)\'\)"\/\>'
    xsl_dir = os.path.split(xsl_filename)[0]
    for line in afile.readlines():
        res = re.findall(pattern, line)
        if res:
            relative = res[0]
            url = 'https://portal.rosreestr.ru/xsl/GKN/Vidimus/07/' + relative
            if _is_downloaded(url):
                continue
            filepath = os.path.join(xsl_dir, relative)
            _make_dirs_tree(filepath)
            download_file(url, filepath)
            _add_to_downloaded(url)


def _make_dirs_tree(relative):
    dirname, _ = os.path.split(relative)
    with contextlib.suppress(FileExistsError):
        os.makedirs(dirname)


def get_html(xml_filename, to_file=True):
    # xml_filename = '../Response-80-144513894/kv_00a0c311-76c1-4178-aaad-b85f85d3b5f9.xml'
    # os.chdir('xml_converter')
    xsl_filename = _get_xsl_filename(xml_filename)
    download_dependencies(xsl_filename)
    dom = ET.parse(xml_filename)
    xslt = ET.parse(xsl_filename)
    transform = ET.XSLT(xslt)
    newdom = transform(dom)
    # result_file = 'result.html'
    # # if to_file:
    # #     with open(result_file, 'wb') as wb:
    # #         wb.write(ET.tostring(newdom, pretty_print=True))
    # #     print(os.getcwd())
    # #     return result_file
    return ET.tostring(newdom, pretty_print=True)


if __name__ == '__main__':
    get_html('../Response-80-144513894/kv_00a0c311-76c1-4178-aaad-b85f85d3b5f9.xml')


# 'schema/KVZU_v07/SchemaCommon/dCategories_v01.xsd'
# 'https://portal.rosreestr.ru/xsl/EGRP/Reestr_Extract_Big/ZU/07/Common.xsl'

# https://portal.rosreestr.ru/xsl/EGRP/schema/KVZU_v07/SchemaCommon/dCategories_v01.xsd
# https://portal.rosreestr.ru/xsl/EGRP/Reestr_Extract_Big/ZU/07/Common.xsl

# https://portal.rosreestr.ru/xsl/GKN/Vidimus/07/schema/KVZU_v07/SchemaCommon/dCategories_v01.xsd
# https://portal.rosreestr.ru/xsl/GKN/Vidimus/07/dict/months.xml
