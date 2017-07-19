# -*- coding: utf-8 -*-

import io
import os
import zipfile

import requests


def update_language(lang='pl'):
    response = requests.get(
        'https://crowdin.com/'
        'download/project/django-girls-tutorial/{}.zip'.format(lang),
        stream=True,
    )

    with zipfile.ZipFile(io.BytesIO(response.content)) as zip_f:
        for src_name in zip_f.namelist():
            if src_name.endswith('/'):
                continue

            dst_name = os.path.join(
                'tutorial',
                lang,
                *os.path.normpath(src_name).split(os.sep)[1:]
            )
            with open(dst_name, 'wb') as dst_f:
                dst_f.write(zip_f.read(src_name))


if __name__ == '__main__':
    update_language()
