# ulauncher-notion-search

Quickly search Notion pages using Ulauncher.

## Install

### Requirements

- [Ulauncher 5](https://ulauncher.io/)
- Python >= 3
- `requests` package. Install this using `pip install requests`
- `rapidfuzz` package. Install this using `pip install rapidfuzz`
- [Notion app](https://github.com/notion-enhancer/notion-repackaged) (optional).

### Steps

1. Ulauncher > Preferences > Extensions > Add extension

2. Paste the following URL:

    ```
    https://github.com/hakonmh/ulauncher-notion-search
    ```

3. Go to [Notion Integration](https://www.notion.so/my-integrations), create an integration and [follow the instructions](https://developers.notion.com/docs/getting-started#getting-started) to link the token with a page.

4. Allow a page to be searched: Go to the page > `...` in the top right hand corner > Add connections > Add your Notion integration

    - You only need to do this for top level pages. The integration gets access to all child pages.

5. Copy the integration token into the *Notion Token* field in the Notion Search settings.

    - Multiple tokens can be specified by using `,` as a delimiter.

This extension should now be set up and work.

## Usage

Default keyword to trigger this extension is **`nt`**. This can be changed in the preferences.

## License

This source code is released under the [MIT](LICENSE) license.
