from dataclasses import dataclass
import json
import asyncio
import logging
import aiohttp
from thefuzz.fuzz import WRatio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class NotionPage:
    """Represents a Notion page with essential metadata."""
    title: str
    url: str
    workspace_name: str

    def to_dict(self):
        """Convert the NotionPage to a dictionary format."""
        return {
            'title': self.title,
            'url': self.url,
            'workspace_name': self.workspace_name
        }

class NotionClient:
    """Handles HTTP communication with Notion API."""

    NOTION_API_VERSION = "2022-06-28"
    BASE_URL = "https://api.notion.com/v1"

    def __init__(self, session, token):
        self.session = session
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": self.NOTION_API_VERSION,
            "Content-Type": "application/json"
        }
        logger.debug(f"Initialized NotionClient with API version {self.NOTION_API_VERSION}")

    async def get_user_info(self):
        """Fetch current user information."""
        url = f"{self.BASE_URL}/users/me"
        logger.debug("Fetching user info")
        try:
            async with self.session.get(url, headers=self.headers) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch user info. Status: {response.status}")
                    return {'name': 'Unknown Workspace'}
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"Network error while fetching user info: {e}")
            return {'name': 'Unknown Workspace'}

    async def search_pages(self, query):
        """Search for pages matching the query."""
        url = f"{self.BASE_URL}/search"
        body = json.dumps({"query": query, 'page_size': 50})

        logger.debug(f"Searching pages with query: {query}")
        try:
            async with self.session.post(url, headers=self.headers, data=body) as response:
                if response.status != 200:
                    logger.error(f"Search request failed. Status: {response.status}")
                    return {"results": []}

                results = await response.json()
                if 'results' not in results:
                    logger.warning("Missing 'results' key in API response")
                    return {"results": []}

                logger.debug(f"Found {len(results['results'])} results")
                return results
        except aiohttp.ClientError as e:
            logger.error(f"Network error during search: {e}")
            return {"results": []}

class NotionPageParser:
    """Handles parsing of Notion API responses into NotionPage objects."""

    @staticmethod
    def parse_pages(results, workspace_name):
        """Parse API results into NotionPage objects."""
        if not results.get("results"):
            logger.debug("No results to parse")
            return []

        pages = []
        for result in results["results"]:
            try:
                page = NotionPage(
                    title=NotionPageParser._extract_title(result),
                    url=result['url'],
                    workspace_name=workspace_name
                )
                pages.append(page)
            except Exception as e:
                logger.error(f"Failed to parse page: {str(e)}", exc_info=True)
                continue

        logger.debug(f"Successfully parsed {len(pages)} pages")
        return pages

    @staticmethod
    def _extract_title(result):
        """Extract title from various Notion object types."""
        if result['object'] == 'database':
            return NotionPageParser._get_db_title(result)

        parent_type = result['parent']['type']
        if parent_type == 'database_id':
            return NotionPageParser._get_db_child_title(result)
        return NotionPageParser._get_page_title(result)

    @staticmethod
    def _get_db_title(result):
        try:
            return result['title'][0]['plain_text']
        except (IndexError, KeyError):
            return ''

    @staticmethod
    def _get_db_child_title(result):
        properties = result['properties']
        for prop in properties.values():
            if prop['type'] == 'title':
                try:
                    return prop['title'][0]['plain_text']
                except (IndexError, KeyError):
                    return ''
        return ''

    @staticmethod
    def _get_page_title(result):
        try:
            title_parts = result['properties']['title']['title']
            return ''.join(t['plain_text'] for t in title_parts)
        except (KeyError, TypeError):
            return ''

class NotionSearch:
    """Main class for searching across multiple Notion workspaces."""

    def __init__(self, tokens):
        """Initialize with comma-separated Notion API tokens."""
        self.workspace_info = {}
        self.tokens = [t.strip() for t in tokens.split(',')]
        logger.info(f"Initializing NotionSearch with {len(self.tokens)} tokens")
        asyncio.run(self._initialize_workspaces())

    async def _initialize_workspaces(self):
        """Fetch workspace information for all tokens."""
        logger.debug("Initializing workspaces")
        async with aiohttp.ClientSession() as session:
            tasks = []
            for token in self.tokens:
                client = NotionClient(session, token)
                tasks.append(self._fetch_workspace_info(client, token))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            successful_workspaces = 0
            for token, name in results:
                if isinstance(name, Exception):
                    logger.error(f"Failed to initialize workspace: {str(name)}")
                    continue
                self.workspace_info[token] = name
                successful_workspaces += 1

            logger.info(f"Successfully initialized {successful_workspaces}/{len(self.tokens)} workspaces")

    async def _fetch_workspace_info(self, client, token):
        """Fetch workspace name for a single token."""
        try:
            results = await client.get_user_info()
            workspace_name = results.get('name', 'Unknown Workspace')
            logger.debug(f"Fetched workspace info: {workspace_name}")
            return token, workspace_name
        except Exception as e:
            logger.error(f"Error fetching workspace info: {str(e)}")
            return token, e

    def search(self, query):
        """
        Search across all Notion workspaces.

        Args:
            query: Search term to look for in Notion pages

        Returns:
            List of dictionaries containing page information
        """
        if not query:
            logger.debug("Empty search query, returning empty results")
            return []

        logger.info(f"Searching for: {query}")
        pages = asyncio.run(self._search(query.lower()))
        logger.info(f"Found {len(pages)} matching pages")
        return pages

    async def _search(self, query):
        """Perform search across all workspaces asynchronously."""
        logger.debug("Starting search across workspaces")
        async with aiohttp.ClientSession() as session:
            tasks = []
            for token in self.workspace_info:
                client = NotionClient(session, token)
                tasks.append(self._search_workspace(client, token, query))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_pages = []
            failed_searches = 0
            for pages in results:
                if isinstance(pages, Exception):
                    logger.error(f"Search failed in workspace: {str(pages)}")
                    failed_searches += 1
                    continue
                all_pages.extend(pages)

            if failed_searches:
                logger.warning(f"Search failed in {failed_searches} workspace(s)")

            logger.debug(f"Found total of {len(all_pages)} pages before sorting")
            return self._sort_by_relevance(all_pages, query)

    async def _search_workspace(self, client, token, query):
        """Search within a single workspace."""
        workspace_name = self.workspace_info[token]
        logger.debug(f"Searching workspace: {workspace_name}")
        results = await client.search_pages(query)
        pages = NotionPageParser.parse_pages(results, workspace_name)
        logger.debug(f"Found {len(pages)} pages in workspace: {workspace_name}")
        return pages

    def _sort_by_relevance(self, pages, query):
        """Sort pages by title relevance and return top 10."""
        scored_pages = [(page, WRatio(page.title, query)) for page in pages]
        scored_pages.sort(key=lambda x: x[1], reverse=True)
        top_pages = [page for page, _ in scored_pages[:10]]
        logger.debug(f"Returning top {len(top_pages)} most relevant results")
        return top_pages
