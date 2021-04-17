import io
import os
import zipfile
from time import sleep

import requests
from git import Repo

import secrets


language_transition = {
    # "cs-CZ": "cs",
    "de-DE": "de",
    # "es-ES": "es",
    # "fr-FR": "fr",
    # "hu-HU": "hu",
    # "it-IT": "it",
    # "ko-KR": "ko",
    # "pl-PL": "pl",
    # "pt-BR": "pt",
    # "ru-RU": "ru",
    # "sk-SK": "sk",
    # "tr-TR": "tr",
    # "uk-UA": "uk",
    # "zh-CN": "zh",
}


class Crowdin(object):
    def __init__(self, project_id, access_token):
        self.project_id = project_id
        self.access_token = access_token

    def build(self):
        build_data = requests.post(
            f"https://api.crowdin.com/api/v2/projects/{self.project_id}/translations/builds",
            headers={
                "Content-type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
            },
        ).json()["data"]

        while build_data["status"] != "finished":
            sleep(5)
            build_data = requests.get(
                f"https://api.crowdin.com/api/v2/projects/{self.project_id}/translations/builds/{build_data['id']}",
                headers={
                    "Content-type": "application/json",
                    "Authorization": f"Bearer {self.access_token}",
                },
            ).json()["data"]

        self.build_id = build_data["id"]

    def download(self, lang):
        link = requests.get(
            f"https://api.crowdin.com/api/v2/projects/{self.project_id}/translations/builds/{self.build_id}/download",
            headers={
                "Content-type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
            },
        ).json()["data"]["url"]

        return zipfile.ZipFile(io.BytesIO(requests.get(link).content))


if __name__ == "__main__":
    c = Crowdin(secrets.PROJECT_ID, secrets.ACCESS_TOKEN)

    repo = Repo(os.path.join(os.path.dirname(__file__), "tutorial"))
    c.build()
    for code in language_transition:
        repo.heads.master.checkout()
        repo.create_head("crowdin-translation-{}".format(language_transition[code]))
        repo.heads[
            "crowdin-translation-{}".format(language_transition[code])
        ].checkout()

        with c.download(code) as zip_f:
            for src_name in zip_f.namelist():
                if not src_name.startswith(f"master/{code}"):
                    continue

                dst_name = os.path.join(
                    "tutorial",
                    language_transition[code],
                    *os.path.normpath(src_name).split(os.sep)[2:],
                )

                if src_name.endswith("/"):
                    if not os.path.exists(dst_name):
                        os.makedirs(dst_name)
                    continue

                with open(dst_name, "bw+") as dst_f:
                    print(f"{src_name} -> {dst_name}")
                    dst_f.write(zip_f.read(src_name))
                repo.index.add(
                    [
                        os.path.join(
                            language_transition[code],
                            *os.path.normpath(src_name).split(os.sep)[2:],
                        )
                    ]
                )
