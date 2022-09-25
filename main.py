from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

from notion_search import Notion
from os import system


class NotionSearch(Extension):
    NOTION = None

    def __init__(self):
        super(NotionSearch, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):

    def on_event(self, event, extension):
        items = []

        if not extension.NOTION:
            notion_token = extension.preferences.get("notion_token")
            extension.NOTION = Notion(notion_token)
        text = event.get_argument()
        pages = extension.NOTION.search(text)
        for page in pages:
            item = ExtensionResultItem(icon="images/icon.png",  # page['icon'],
                                       name=page['title'],
                                       description=page['description'],
                                       on_enter=ExtensionCustomAction(page))
            items.append(item)
        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        page = event.get_data()
        open_in = extension.preferences.get("open_in").lower()
        if open_in == 'app':
            system(f"notion-app {page['url']} &")
        else:
            system(f"xdg-open {page['url']} &")


if __name__ == '__main__':
    NotionSearch().run()
