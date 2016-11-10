import os

from prism.api.view import BaseView, subroute

class OverviewView(BaseView):
    def __init__(self):
        BaseView.__init__(self, endpoint='/general', title='Overview',
                                menu={'id': 'sso.overview', 'icon': 'Overview', 'order': 0,
                                        'parent': {'id': 'sso', 'text': 'SAML', 'icon': 'bullhorn'}})

    def get(self, request):
        return ('general_info.html')
