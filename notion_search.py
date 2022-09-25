import httpx
from thefuzz.fuzz import partial_ratio


class Notion:
    TOKEN = ''
    RESULTS_ALREADY_SEARCHED = []

    def __init__(self, token, ):
        tokens = token.split(',')
        tokens = [t.replace(' ', '') for t in tokens]
        self.tokens = []
        for token in tokens:
            self.tokens.append((token, self._get_workspace(token)))

    def _get_workspace(self, token):
        headers = {"Authorization": f"Bearer {token}",
                   "Notion-Version": "2022-06-28"}
        response = httpx.get("https://api.notion.com/v1/users/me",
                             headers=headers)
        description = response.json()['name']
        return description

    def search(self, text):
        if text is None or text == '':
            return []
        text = text.lower()
        pages = []
        for token, description in self.tokens:
            results = self.call_notion_api(token, text)
            new_pages = self.parse_results(results, description)
            pages.extend(new_pages)
        pages = self.filter_pages(pages, text)
        return pages

    def call_notion_api(self, token, text):
        headers = {"Authorization": f"Bearer {token}",
                   "Notion-Version": "2022-06-28"}
        body = {"query": text, 'page_size': 10}
        response = httpx.post("https://api.notion.com/v1/search",
                              headers=headers, json=body)
        return response.json()

    def parse_results(self, results, description):
        pages = []
        for result in results["results"]:
            page = {
                'title': self._get_title(result),
                'url': self._get_url(result),
                'icon': self._get_icon(result),
                'description': f'Integration:  {description}'
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
        title_ = result['properties']['title']['title']
        title = ''
        for t in title_:
            title = title + t['plain_text']
        return title

    def _get_url(self, result):
        return result['url']

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

    def filter_pages(self, pages, text):
        """Returns the 10 pages with highest fuzzy rating"""
        pages = [(p, partial_ratio(p['title'].lower(), text)) for p in pages]
        pages.sort(key=lambda x: x[1], reverse=True)
        pages = [p[0] for p in pages[:10]]
        return pages[:10]
