import os

from ad_server.renderers.creative_renderer import BaseCreativeRenderer
# NOTE: appengine specific, but can be just django
from google.appengine.ext.webapp import template

class BaseHtmlRenderer(BaseCreativeRenderer):
    """
    All HTML renderers will need to subclass this.

    Inheritance Hierarchy:
    BaseHtmlRenderer => BaseCreativeRenderer

    NOTE: If the creative type to be rendered has an html_data field
    you should subclass HtmlDataRenderer (which subclasses BaseHtmlRenderer)
    rather than subclassing BaseHtmlRenderer directly
    """

    TEMPLATE = 'common/base.html'

    def __init__(self, *args, **kwargs):
        """
        Calls super __init__ as well as initializes html_context.
        html_context is an html renderer specific property
        used for rendering the html via django template
        """
        super(BaseHtmlRenderer, self).__init__(*args, **kwargs)

        self.html_context = {}
        self._setup_html_context()

    def _get_creative_height(self):
        """
        Gets creative height from the creative object
        """
        return int(self.creative.height) if self.creative.height else 0

    def _get_creative_width(self):
        """
        Gets creative width from the creative object
        """
        return int(self.creative.width) if self.creative.width else 0

    def _setup_html_context(self):
        """
        Initialize the html specific properties necessary for rendering
        html creative using django template. This method may need to be overridden.
        """
        self.html_context['creative'] = self.creative
        self.html_context['version'] = self.version
        self.html_context['impression_url'] = self.impression_url
        self.html_context['is_fullscreen'] = self.adunit.is_fullscreen()
        self.html_context['is_tablet'] = self.adunit.is_tablet()

        creative_height = self._get_creative_height()
        creative_width = self._get_creative_width()

        self.html_context['w'] = creative_width
        self.html_context['h'] = creative_height
        self.html_context['w_divided_2'] = creative_width/2
        self.html_context['h_divided_2'] = creative_height/2

        self.html_context['os'] = self._get_os_type()
        self.html_context['use_impression_pixel'] = self.\
                                                _should_use_impression_pixel()
        self.html_context['use_center_style'] = self.\
                                                _should_use_center_style()

    def _get_os_type(self):
        """
        Gets the os type based on how the app was registered in our
        system.
        """
        app_type = self.adunit.app.app_type

        if app_type in ['iphone', 'ipad']:
            return 'ios'
        return app_type

    def _should_use_center_style(self):
        """
        Due to SDK changes various version of the mopub client can and/or
        cannot support centering of smaller creatives inside of fullscreen
        adunits.
        """
        os_type = self._get_os_type()
        # if the creative is explicity 'full' ,
        # creative_height = creative_width = 0
        creative_height = self._get_creative_height()
        creative_width = self._get_creative_width()
        return self.adunit.is_fullscreen() and creative_width \
                    and creative_height and os_type == 'ios' \
                    and self.version >= 7

    def _should_use_impression_pixel(self):
        """
        Due to SDK changes various mopub clients expect either the impression
        to be tracked by the HTML or the native code.

        Returns True if the HTML should contain an image tag with the
        appropriate impression tracking url
        """
        os_type = self._get_os_type()
        is_fullscreen = self.adunit.is_fullscreen()
        return (os_type in ['mweb', 'android'] or not is_fullscreen)

    def _get_ad_type(self):
        return 'html'

    def _setup_headers(self):
        super(BaseHtmlRenderer, self)._setup_headers()
        self.header_context.ad_type = self._get_ad_type()
        self.header_context.full_ad_type = None

    def _get_template(self):
        return self.TEMPLATE

    def _setup_content(self):
        """
        Uses the html_context and self.TEMPLATE to generate creative html.
        This method should never be overridden. In order to customize
        html creative rendering, you should override _setup_html_context
        to provide specific context to the template. You can also
        override self.TEMPLATE to provide more flexibility/customization
        """
        path = os.path.join(os.path.dirname(__file__),
                            'templates',
                            self._get_template()
                            )
        self.rendered_creative = template.render(path, self.html_context)

