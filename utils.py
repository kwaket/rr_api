import requests
import zipfile


def download_file(url, filename):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return filename


def unzip_file(zip_path, dest_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(dest_path)
    return dest_path


def get_zip_content_list(zip_path):
    f = zipfile.ZipFile(zip_path)
    return f.namelist()
