from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction

from notion_search import Notion
from os import system


class NotionSearch(Extension):
    NOTION = None

    def __init__(self):
        super(NotionSearch, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):
    TOKEN = '~'

    def on_event(self, event, extension):
        extension = self._run_extension(extension)
        try:
            items = self._fetch_items(event, extension)
        except Exception as e:
            items = self._show_error_info(e)
        return RenderResultListAction(items)

    def _run_extension(self, extension):
        notion_token = extension.preferences.get("notion_token")
        if not extension.NOTION or notion_token != self.TOKEN:
            self.TOKEN = notion_token
            extension.NOTION = Notion(self.TOKEN)
        return extension

    def _fetch_items(self, event, extension):
        items = []
        text = event.get_argument()
        pages = extension.NOTION.search(text)
        for page in pages:
            item = ExtensionResultItem(icon="images/icon.png",
                                       name=page['title'],
                                       description=page['description'],
                                       on_enter=ExtensionCustomAction(page))
            items.append(item)
        return items

    def _show_error_info(self, e):
        name = str(type(e)).split("'")[1]
        description = str(e)
        item = ExtensionResultItem(icon="images/icon.png",
                                   name=name,
                                   description=description,
                                   on_enter=DoNothingAction())
        return [item]


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        url = event.get_data()['url']
        open_in = extension.preferences.get("open_in").lower()
        if open_in == 'app':
            url = url.replace('https', 'notion')
            url = url.replace('http', 'notion')
        system(f"xdg-open {url} &")


if __name__ == '__main__':
    NotionSearch().run()
