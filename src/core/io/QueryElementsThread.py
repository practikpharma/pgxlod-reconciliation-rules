import threading

from core.io.ServerManager import ServerManager

__author__ = "Pierre Monnin"


class QueryElementsThread(threading.Thread):
    def __init__(self, configuration_parameters, max_rows, query):
        threading.Thread.__init__(self)
        self._server_manager = ServerManager(configuration_parameters, max_rows)
        self._query = query
        self._results = set()

    def run(self):
        self._results = set(self._server_manager.query_elements(self._query))

    def get_results(self):
        return self._results
