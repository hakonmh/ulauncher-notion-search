from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.OpenUrlAction import OpenUrlAction

from notion_search import Notion


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
            extension.NOTION = Notion(extension.preferences.get("notion_token"))
        data = event.get_argument()
        open_in = extension.preferences.get("open_in")
        pages = extension.NOTION.search(data, open_in)
        for page in pages:
            item = ExtensionResultItem(icon=page['icon'],
                                       name=page['title'],
                                       on_enter=ExtensionCustomAction(page))
            items.append(item)

        return RenderResultListAction(items)


class ItemEnterEventListener(EventListener):

    def on_event(self, event, extension):
        page = event.get_data()
        return RenderResultListAction([
            ExtensionResultItem(on_enter=OpenUrlAction(page['url']))
        ])


if __name__ == '__main__':
    NotionSearch().run()
