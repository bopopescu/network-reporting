from ad_server.renderers.base_html_renderer import BaseHtmlRenderer
from google.appengine.api import images
from google.appengine.api.images import InvalidBlobKeyError

from common.utils import helpers
import logging

class TextAndTileRenderer(BaseHtmlRenderer):
    """
    Uses specific TEMPLATE for rendering text/tile creative

    Inheritance Hierarchy:
    TextAndTileRenderer => BaseHtmlRenderer => BaseCreativeRenderer
    """
    TEMPLATE = 'text_tile.html'

    def _setup_html_context(self):
        super(TextAndTileRenderer, self)._setup_html_context()
        if hasattr(self.creative, 'image_serve_url'):
            image_url = self.creative.image_serve_url
        else:
            try:
                image_url = helpers.get_url_for_blob(self.creative.image_blob,
                                                     ssl=False)
            except InvalidBlobKeyError:
                logging.error("Could not find blobkey."\
                              " Perhaps you are on mopub-experimental.")
                image_url = ""
            except NotImplementedError:
                image_url = "http://localhost:8080/_ah/img/blobby"

        self.html_context["image_url"] = image_url