import json
import requests


class Notion:
    TOKEN = ''
    RESULTS_ALREADY_SEARCHED = []

    def __init__(self, token):
        tokens = token.split(',')
        tokens = [t.replace(' ', '') for t in tokens]
        self.tokens = tokens

    def search(self, text, open_in):
        pages = []
        for token in self.tokens:

            response = requests.post("https://api.notion.com/v1/search",
                                     headers={"Authorization": f"Bearer {token}",
                                              "Notion-Version": "2022-06-28",
                                              },
                                     data=json.dumps({"page_size": '10'})
                                     )
            results = response.json()["results"]
            for result in results[:10]:
                page = {
                    'title': self.get_title(result),
                    'url': self.get_url(result, open_in),
                    'icon': self.get_icon(result)
                }

                pages.append(page)

        return pages

    def get_title(self, result):
        return result['properties']['title']['title'][0]['plain_text']

    def get_url(self, result, open_in):
        url = result['url']
        if open_in == 'app':
            url = url.replace('https', 'notion')
        elif open_in == 'browser':
            pass
        else:
            raise ValueError('open_in must either be app or browser')
        return url

    def get_icon(self, result):
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
