from ad_server.renderers.base_html_renderer import BaseHtmlRenderer

from google.appengine.api.images import InvalidBlobKeyError

from common.utils import helpers
import logging

class ImageRenderer(BaseHtmlRenderer):
    """
    Uses image specific TEMPLATE for rendering image creative

    Inheritance Hierarchy:
    ImageRenderer => BaseHtmlRenderer => BaseCreativeRenderer
    """

    TEMPLATE = 'image.html'

    def _get_creative_width(self):
        """
        Gets creative width from the image meta data
        """
        return self.creative.image_width

    def _get_creative_height(self):
        """
        Gets creative width from the image meta data
        """
        return self.creative.image_height

    def _setup_html_context(self):
        super(ImageRenderer, self)._setup_html_context()
        if hasattr(self.creative, 'image_serve_url'):
            image_url = self.creative.image_serve_url
        else:
            try:
                image_url = helpers.get_url_for_blob(self.creative.image_blob,
                                                     ssl=False)
            except InvalidBlobKeyError:
                logging.error("Could not find blobkey. "\
                              "Perhaps you are on mopub-experimental.")
                image_url = ""
            except NotImplementedError:
                image_url = "http://localhost:8080/_ah/img/blobby"

        self.html_context["image_url"] = image_url
