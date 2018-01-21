# -*- coding: utf-8 -*-

import io
import os
import zipfile

import requests
from git import Repo

import secrets


class Crowdin(object):

    _supported_languages = None
    _translation_status = None

    def __init__(self, project_identifier, project_key):
        self.project_identifier = project_identifier
        self.project_key = project_key

    @classmethod
    def supported_languages(cls):
        if cls._supported_languages is None:
            cls._supported_languages = {
                language['crowdin_code']: language
                for language in requests.get(
                    'https://api.crowdin.com/api/supported-languages?json=mycallback'
                ).json()
            }
        return cls._supported_languages

    def translation_status(self):
        if self._translation_status is None:
            self._translation_status = {
                language['code']: language
                for language in requests.post(
                    'https://api.crowdin.com/api/project/'
                    '{project_identifier}/status?key={project_key}&json=mycallback'.format(
                        project_identifier=self.project_identifier,
                        project_key=self.project_key,
                    )
                ).json()
            }
        return self._translation_status

    def export(self):
        return requests.get(
            'https://api.crowdin.com/api/project/'
            '{project_identifier}/export?key={project_key}&json=mycallback'.format(
                project_identifier=self.project_identifier,
                project_key=self.project_key,
            )
        ).json()

    def download(self, lang):
        response = requests.get(
            'https://api.crowdin.com/api/project/'
            '{project_identifier}/download/{lang}.zip?key={project_key}'.format(
                project_identifier=self.project_identifier,
                project_key=self.project_key,
                lang=lang,
            ),
            stream=True,
        )
        return zipfile.ZipFile(io.BytesIO(response.content))


if __name__ == '__main__':
    c = Crowdin(secrets.PROJECT_IDENTIFIER, secrets.PROJECT_KEY)

    two_letter_code_occurs = {}
    for code, language in c.translation_status().items():
        two_letter_code = c.supported_languages()[code]['iso_639_1']
        two_letter_code_occurs[two_letter_code] = two_letter_code_occurs.get(
            two_letter_code, 0
        ) + 1
    language_transition = {
        code: c.supported_languages()[code]['iso_639_1']
        if two_letter_code_occurs[c.supported_languages()[code]['iso_639_1']] == 1
        else c.supported_languages()[code]['locale']
        for code in c.translation_status()
    }

    repo = Repo(os.path.join(os.path.dirname(__file__), 'tutorial'))
    c.export()
    for code in c.translation_status():
        repo.heads.master.checkout()
        repo.create_head('crowdin-translation-{}'.format(
            language_transition[code]
        ))
        repo.heads['crowdin-translation-{}'.format(
            language_transition[code]
        )].checkout()

        with c.download(code) as zip_f:
            for src_name in zip_f.namelist():
                dst_name = os.path.join(
                    'tutorial',
                    language_transition[code],
                    *os.path.normpath(src_name).split(os.sep)[2:]
                )

                if src_name.endswith('/'):
                    if not os.path.exists(dst_name):
                        os.makedirs(dst_name)
                    continue

                with open(dst_name, 'bw+') as dst_f:
                    dst_f.write(zip_f.read(src_name))
                repo.index.add([os.path.join(
                    language_transition[code],
                    *os.path.normpath(src_name).split(os.sep)[2:]
                )])
        repo.index.commit('crowdin-translation-{}'.format(
            language_transition[code]
        ))
