import requests
from rapidfuzz.fuzz import partial_ratio


class Notion:
    TOKEN = ''
    RESULTS_ALREADY_SEARCHED = []

    def __init__(self, token, open_in='app'):
        tokens = token.split(',')
        tokens = [t.replace(' ', '') for t in tokens]
        self.tokens = tokens
        self.open_in = open_in

    def search(self, text):
        text = text.lower()
        pages = []
        for token in self.tokens:
            results = self.call_notion_api(token, text)
            new_pages = self.parse_results(results)
            pages.extend(new_pages)
        pages = self.filter_pages(pages, text)  # Include text later?
        return pages

    def get_num_results_per_token(self):
        num_results = [10 // len(self.tokens)] * len(self.tokens)
        i = 0
        while sum(num_results) < 10:
            num_results[i] += 1
            i += 1
        return num_results

    def call_notion_api(self, token, text):
        response = requests.post("https://api.notion.com/v1/search",
                                 headers={"Authorization": f"Bearer {token}",
                                          "Notion-Version": "2022-06-28"},
                                 json={"query": text}
                                 )
        return response.json()

    def parse_results(self, results):
        pages = []
        for result in results["results"]:
            page = {
                'title': self._get_title(result),
                'url': self._get_url(result),
                'icon': self._get_icon(result)
            }
            pages.append(page)
        return pages

    def _get_title(self, result):
        if result['object'] == 'database':
            title = self.__get_db_title(result)
        else:
            parent_type = result['parent']['type']
            if parent_type == 'database_id':
                title = self.__get_db_child_title(result)
            else:
                title = self.__get_page_title(result)
        return title

    def __get_db_title(self, result):
        try:
            title = result['title'][0]['plain_text']
        except IndexError:  # No title defined
            title = ''
        return title

    def __get_db_child_title(self, result):
        properties = result['properties']
        for prop in properties.keys():
            if properties[prop]['type'] == 'title':
                try:
                    title = properties[prop]['title'][0]['plain_text']
                except IndexError:  # No title defined
                    title = ''
                break
        return title

    def __get_page_title(self, result):
        return result['properties']['title']['title'][0]['plain_text']

    def _get_url(self, result):
        url = result['url']
        if self.open_in == 'app':
            url = url.replace('https', 'notion')
        elif self.open_in == 'browser':
            pass
        else:
            raise ValueError('open_in must either be app or browser')
        return url

    def _get_icon(self, result):
        icon_data = result['icon']
        if icon_data is None:
            icon = None
        elif icon_data['type'] == 'file':
            icon = icon_data['file']['url']
        elif icon_data['type'] == 'emoji':
            icon = icon_data['emoji']
        else:
            icon = 'images/icon.png'
        return icon

    def filter_pages(self, _pages, text):
        """Returns the 10 pages with highest fuzzy rating"""
        pages = [(p, partial_ratio(p['title'].lower(), text)) for p in _pages]
        pages.sort(key=self._key, reverse=True)
        pages = [p[0] for p in pages[:10]]
        return pages

    def _key(self, item):
        return item[1]
