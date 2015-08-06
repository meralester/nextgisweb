'''
The code is based on featureserver's code
'''
from lxml import etree
from lxml import objectify

from ...FeatureServer.WebFeatureService.FilterEncoding.FilterEncoding import \
    FilterEncoding
from ...FeatureServer.WebFeatureService.Transaction.Transaction import \
    Transaction
from ...FeatureServer.WebFeatureService.FilterEncoding.Select import Select
from ...FeatureServer.Exceptions.OperationParsingFailedException import \
    OperationParsingFailedException
from ...FeatureServer.Service.Action import Action

from copy import deepcopy


class WFSRequest(object):
    dom = None
    data = ""
    parser = None

    transaction = None
    filter = None

    def __init__(self):
        self.parser = objectify.makeparser(
            remove_blank_text=True, ns_clean=True)

    def parse(self, data):
        self.data = data
        # self.data = self.data.replace('wildCard="*"', 'wildCard="\*"')
        # self.data = self.data.replace('wildCard="?"', 'wildCard="\?"')
        # self.data = self.data.replace('singleChar="*"', 'singleChar="\*"')
        # self.data = self.data.replace('singleChar="?"', 'singleChar="\?"')

        try:
            self.dom = etree.XML(self.data, parser=self.parser)
        except Exception:
            raise OperationParsingFailedException(self.data)

    def render(self, datasource):
        '''
        Renders a FilterEncoding to its SQL
        '''
        query = self.dom.xpath("//*[local-name() = 'Query']")
        if len(query) > 0:
            # query - return a dummy select object
            self.filter = FilterEncoding(deepcopy(query[0]).getchildren()[0])
        else:
            self.filter = FilterEncoding(self.data)

        self.filter.parse()
        return self.filter.render(datasource)

    def getCapabilitiesAction(self):
        '''Returns GetCapabilities action
        '''
        action = Action()
        action.request = 'GetCapabilities'
        if 'version' in self.dom.keys():
            action.version = self.dom.get('version')

        return [action]

    def get_transactions(self):
        '''Returns all WFS-T actions
        '''
        query = self.dom.xpath("//*[local-name() = 'Query']")
        if len(query) > 0:
            # query - return a dummy select object
            return [Select(etree.tostring(deepcopy(query[0]).getchildren()[0]))]
        else:
            # returning all transaction objects in a array
            self.transaction = Transaction()
            self.transaction.parse(self.data)
            return self.transaction.getActions()

    def isGetCapabilities(self):
        '''Check if request is GetCapabilities request
        '''

        if self.dom is None:
            return None

        if self.dom.xpath("//*[local-name() = 'GetCapabilities']"):
            return True
        else:
            return False

    def getActions(self):
        # import ipdb; ipdb.set_trace()
        if self.dom is None:
            return None

        if self.isGetCapabilities():
            return self.get_capabilities()
        else:
            return self.get_transactions()
