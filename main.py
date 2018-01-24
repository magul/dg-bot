# -*- coding: utf-8 -*-

import io
import os
import zipfile

import requests
from git import Repo

import secrets


language_transition = {
    'cs': 'cs',
    'de': 'de',
    # 'en': 'en',
    'es-ES': 'es',
    'fr': 'fr',
    'hu': 'hu',
    'it': 'it',
    'ko': 'ko',
    'pl': 'pl',
    'pt-BR': 'pt',
    'ru': 'ru',
    'sk': 'sk',
    'tr': 'tr',
    'uk': 'uk',
    'zh-CN': 'zh',
}


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

    repo = Repo(os.path.join(os.path.dirname(__file__), 'tutorial'))
    c.export()
    for code in language_transition:
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
