import json
import logging
import socket
import requests
import tqdm

__author__ = "Pierre Monnin"


class ServerManager:
    def __init__(self, configuration_parameters, max_rows):
        self.server_address = configuration_parameters["server-address"]
        self.json_conf_attribute = configuration_parameters["url-json-conf-attribute"]
        self.json_conf_value = configuration_parameters["url-json-conf-value"]
        self.default_graph_attribute = configuration_parameters["url-default-graph-attribute"]
        self.default_graph_value = configuration_parameters["url-default-graph-value"]
        self.query_attribute = configuration_parameters["url-query-attribute"]
        socket.setdefaulttimeout(configuration_parameters["timeout"])
        self.max_rows = max_rows
        self.prefixes = "PREFIX pgxo:<http://pgxo.loria.fr/> " + \
                        "PREFIX rdfs:<http://www.w3.org/2000/01/rdf-schema#> " + \
                        "PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#> " + \
                        "PREFIX owl:<http://www.w3.org/2002/07/owl#> " + \
                        "PREFIX obo:<http://purl.obolibrary.org/obo/> "
        self._logger = logging.getLogger()

    def query_server(self, query):
        done = False

        content = {}

        while not done:
            done = True

            query_parameters = {
                self.json_conf_attribute: self.json_conf_value,
                self.default_graph_attribute: self.default_graph_value,
                self.query_attribute: query
            }

            content = requests.get(self.server_address, query_parameters)

            if content.status_code == 404:
                done = False
                self._logger.critical("404 error. New try...")

            elif content.status_code != 200:
                self._logger.critical(content.content)

        return json.loads(content.text)

    def query_count_elements(self, where_clause):
        results_json = self.query_server(self.prefixes + " select count(distinct ?e) as ?count where { " +
                                         where_clause + " }")

        return int(results_json["results"]["bindings"][0]["count"]["value"])

    def query_count_two_elements(self, where_clause):
        results_json = self.query_server(self.prefixes + " select count(*) as ?count where { "
                                                         "select distinct ?e1 ?e2 where {" + where_clause +
                                                         " } }")
        return int(results_json["results"]["bindings"][0]["count"]["value"])

    def query_elements(self, where_clause):
        ret_val = []
        elements_count = self.query_count_elements(where_clause)

        while len(ret_val) != elements_count:
            ret_val = []
            offset = 0
            while offset <= elements_count:
                results_json = self.query_server(self.prefixes + " select distinct ?e where { " + where_clause
                                                 + " } LIMIT " + str(self.max_rows) + " OFFSET " + str(offset))

                for result in results_json["results"]["bindings"]:
                    ret_val.append(str(result["e"]["value"]))

                offset += self.max_rows

            if len(ret_val) != elements_count:
                self._logger.critical("Number of elements different from count, retry...")

        return ret_val

    def query_two_elements(self, where_clause, verbose=False):
        ret_val = []
        elements_count = self.query_count_two_elements(where_clause)

        if verbose and elements_count != 0:
            pbar = tqdm.tqdm(total=elements_count)

        while len(ret_val) != elements_count:
            ret_val = []
            offset = 0

            while offset <= elements_count:
                results_json = self.query_server(self.prefixes + " select distinct ?e1 ?e2 where { " + where_clause +
                                                 " } LIMIT " + str(self.max_rows) + " OFFSET " + str(offset))

                for result in results_json["results"]["bindings"]:
                    ret_val.append((str(result["e1"]["value"]), str(result["e2"]["value"])))
                    if verbose and elements_count != 0:
                        pbar.update(1)

                offset += self.max_rows

            if len(ret_val) != elements_count:
                self._logger.critical("Number of elements different from count, retry...")

                if verbose and elements_count != 0:
                    pbar.close()
                    pbar = tqdm.tqdm(total=elements_count)

        if verbose and elements_count != 0:
            pbar.close()

        return ret_val

    def sameas_expansion(self, individuals):
        ret_val = set(individuals)
        diff = set(individuals)

        while len(diff) != 0:
            current_set = set(ret_val)

            for i in diff:
                current_set |= set(self.query_elements("?e owl:sameAs <" + i + ">"))
                current_set |= set(self.query_elements("<" + i + "> owl:sameAs ?e"))

            diff = current_set - ret_val
            ret_val = current_set

        return ret_val
