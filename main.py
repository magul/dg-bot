import io
import os
import shutil
import zipfile
from time import sleep

import requests
from git import Repo

import secrets


language_transition = {
    # "cs-CZ": "cs",
    # "de-DE": "de",
    # "es-ES": "es",
    # "fr-FR": "fr",
    # "hu-HU": "hu",
    "hy-AM": "hy",
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
        # repo.heads.master.checkout()
        # repo.create_head("crowdin-translation-{}".format(language_transition[code]))
        # repo.heads[
        #     "crowdin-translation-{}".format(language_transition[code])
        # ].checkout()

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

            # refresh images
            for image in [
                ("css", "images", "bootstrap1.png"),
                ("css", "images", "color2.png"),
                ("css", "images", "final.png"),
                ("css", "images", "font.png"),
                ("css", "images", "margin2.png"),
                ("deploy", "images", "github_get_repo_url_screenshot.png"),
                ("deploy", "images", "new_github_repo.png"),
                ("deploy", "images", "pythonanywhere_account.png"),
                ("deploy", "images", "pythonanywhere_bash_console.png"),
                ("deploy", "images", "pythonanywhere_beginner_account_button.png"),
                ("deploy", "images", "pythonanywhere_create_api_token.png"),
                ("django_admin", "images", "django_admin3.png"),
                ("django_admin", "images", "edit_post3.png"),
                ("django_admin", "images", "login_page2.png"),
                ("django_forms", "images", "csrf2.png"),
                ("django_forms", "images", "drafts.png"),
                ("django_forms", "images", "edit_button2.png"),
                ("django_forms", "images", "edit_form2.png"),
                ("django_forms", "images", "form_validation2.png"),
                ("django_forms", "images", "new_form2.png"),
                ("django_forms", "images", "post_create_error.png"),
                ("django_start_project", "images", "install_worked.png"),
                ("django_templates", "images", "donut.png"),
                ("django_templates", "images", "step1.png"),
                ("django_templates", "images", "step2.png"),
                ("django_templates", "images", "step3.png"),
                ("django_urls", "images", "error1.png"),
                ("django_urls", "images", "url.png"),
                ("django_views", "images", "error.png"),
                ("extend_your_application", "images", "404_2.png"),
                ("extend_your_application", "images", "attribute_error2.png"),
                ("extend_your_application", "images", "does_not_exist2.png"),
                ("extend_your_application", "images", "no_reverse_match2.png"),
                ("extend_your_application", "images", "post_detail2.png"),
                ("extend_your_application", "images", "post_list2.png"),
                ("extend_your_application", "images", "template_does_not_exist2.png"),
                ("how_the_internet_works", "images", "internet_1.png"),
                ("how_the_internet_works", "images", "internet_2.png"),
                ("how_the_internet_works", "images", "internet_3.png"),
                ("how_the_internet_works", "images", "internet_4.png"),
                ("html", "images", "step1.png"),
                ("html", "images", "step3.png"),
                ("html", "images", "step4.png"),
                ("html", "images", "step6.png"),
                ("images", "application.png"),
                ("python_installation", "images", "python-installation-options.png"),
                ("python_installation", "images", "windows-plus-r.png"),
                ("python_introduction", "images", "cupcake.png"),
            ]:
                src_path = os.path.join("tutorial", "en", *image)
                dst_path = os.path.join("tutorial", language_transition[code], *image)
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                shutil.copyfile(src_path, dst_path)

                repo.index.add([os.path.join(language_transition[code], *image)])