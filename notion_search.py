import json
from concurrent.futures import ProcessPoolExecutor, as_completed
import requests
from functools import partial
from thefuzz.fuzz import WRatio


class Notion:

    def __init__(self, token):
        tokens = token.split(',')
        tokens = [t.replace(' ', '') for t in tokens]
        self.tokens = self._get_descriptions(tokens)

    def _get_descriptions(self, tokens):
        tasks = [r for r in self._user_request(tokens)]
        tokens = {}
        for response in self._run_tasks(tasks):
            token = self._get_token(response)
            description = self._get_description(response)
            tokens[token] = description
        return tokens

    def _run_tasks(self, tasks):
        with ProcessPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(task) for task in tasks]
            for future in as_completed(futures):
                yield future.result()

    def _user_request(self, tokens):
        url = "https://api.notion.com/v1/users/me"
        for token in tokens:
            h = {"Authorization": f"Bearer {token}",
                 "Notion-Version": "2022-06-28"}
            yield partial(requests.get, url, headers=h)

    def _get_token(self, response):
        token = response.request.headers['Authorization']
        token = token.replace('Bearer ', '')
        return token

    def _get_description(self, response):
        results = self._decode_response(response)
        description = results['name']
        return description

    def search(self, text):
        if text is None or text == '':
            return []
        text = text.lower()
        return self._search(text)

    def _search(self, text):
        tasks = [r for r in self._search_request(text)]
        pages = []
        for response in self._run_tasks(tasks):
            token = self._get_token(response)
            description = self.tokens[token]
            results = self._decode_response(response)
            new_pages = self._parse_results(results, description)
            pages.extend(new_pages)
        pages = self._filter_pages(pages, text)
        return pages

    def _search_request(self, text):
        url = "https://api.notion.com/v1/search"
        body = json.dumps({"query": text, 'page_size': 50})
        for token in self.tokens.keys():
            h = {"Authorization": f"Bearer {token}",
                 "Notion-Version": "2022-06-28"}
            yield partial(requests.post, url, headers=h, data=body)

    def _decode_response(self, response):
        return response.json()

    def _parse_results(self, results, description):
        pages = []
        for result in results["results"]:
            page = {
                'title': self._get_title(result),
                'url': self._get_url(result),
                'description': description,
            }
            pages.append(page)
        return pages

    def _get_title(self, result):
        if result['object'] == 'database':
            title = self._get_db_title(result)
        else:
            parent_type = result['parent']['type']
            if parent_type == 'database_id':
                title = self._get_db_child_title(result)
            else:
                title = self._get_page_title(result)
        return title

    def _get_db_title(self, result):
        try:
            title = result['title'][0]['plain_text']
        except IndexError:  # No title defined
            title = ''
        return title

    def _get_db_child_title(self, result):
        properties = result['properties']
        for prop in properties.keys():
            if properties[prop]['type'] == 'title':
                try:
                    title = properties[prop]['title'][0]['plain_text']
                except IndexError:  # No title defined
                    title = ''
                break
        return title

    def _get_page_title(self, result):
        title_ = result['properties']['title']['title']
        title = ''
        for t in title_:
            title = title + t['plain_text']
        return title

    def _get_url(self, result):
        return result['url']

    def _filter_pages(self, pages, text):
        """Returns the 10 pages with highest fuzzy rating"""
        pages = [(p, WRatio(p['title'], text)) for p in pages]
        pages.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in pages[:10]]
