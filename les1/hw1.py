import time
import json
from pathlib import Path
import requests


class Parse5ka:
    params = {
        "records_per_page": 20
    }

    def __init__(self, start_url: str, save_path: Path):
        self.start_url = start_url
        self.save_path = save_path

    def _get_response(self, url, *args, **kwargs) -> requests.Response:
        while True:
            response = requests.get(url, *args, **kwargs)
            if response.status_code == 200:
                return response
            time.sleep(1)

    def run(self):
        for product in self._parse(self.start_url):
            self._save(product)

    def _parse(self, url):
        while url:
            response = self._get_response(url, params=self.params)
            data = response.json()
            url = data.get('next')
            for product in data.get('results', []):
                yield product

    def _save(self, data):
        file_path = self.save_path.joinpath(f'{data["id"]}.json')
        file_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class CategoryParse5ka(Parse5ka):

    def __init__(self, category_url, *args, **kwargs):
        self.category_url = category_url
        super().__init__(*args, **kwargs)

    def run(self):
        for category in self._get_categories():
            category['products'] = []
            params = f"?categories={category['parent_group_code']}"
            url = f"{self.start_url}{params}"

            category["products"].extend(list(self._parse(url)))
            file_name = f"{category['parent_group_code']}.json"
            cat_path = self.save_path.joinpath(file_name)
            self._save(category, cat_path)

    def _get_categories(self):
        responce = self._get_response(self.category_url)
        data = responce.json()
        return data

    def _save(self, data, cat_path):
        cat_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def get_save_path(dir_name):
    save_path = Path(__file__).parent.joinpath(dir_name)
    if not save_path.exists():
        save_path.mkdir()
    return save_path


if __name__ == '__main__':

    url = 'https://www.5ka.ru/api/v2/special_offers/'
    cat_url = 'https://www.5ka.ru/api/v2/categories/'
    save_path_products = get_save_path('../products')

    if not save_path_products.exists():
        save_path_products.mkdir()

    save_path_categories = get_save_path('../categories')
    parser_products = Parse5ka(url, save_path_products)
    cat_parser = CategoryParse5ka(cat_url, url, save_path_categories)
    cat_parser.run()

