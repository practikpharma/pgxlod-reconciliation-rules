import logging
import queue
import tqdm

__author__ = "Pierre Monnin"


class RDFGraph:
    """
    Represents several adjacencies in the RDF Graph from the triplestore. It is not exactly the RDF Graph from
    the triplestore as only a subset of the triples are queried, some adjacencies are expanded and some predicates
    are considered together (for exemple partOf adjacency can be built from several predicates).
    """

    def __init__(self, cache_manager, server_manager, integration_ontology, part_of_predicates, has_part_predicates,
                 depends_on_predicates):
        """
        Builds the local RDFGraph model
        - owl:sameAs adjacency is expanded with symmetry and transitivity
        - type adjacency is expanded with owl:sameAs and rdfs:subClassOf adjacencies
        - linking predicates adjacencies are expanded following the linking predicates hierarchy and inverses
        :param cache_manager: global cache for the scripts (URI <-> node index in the graph)
        :param server_manager: the server manager object to send SPARQL queries to the triplestore
        :param integration_ontology: the integration ontology used to represent relationships
        :param part_of_predicates: list of predicates used for partOf adjacency
        :param has_part_predicates: list of predicates used for inversely completing partOf adjacency
        :param depends_on_predicates: list of predicates used for dependsOn adjacency
        """

        self._cache_manager = cache_manager

        self._sameas_adjacency = {}

        self._subclassof_adjacency = {}
        self._type_adjacency = {}

        self._partOf_adjacency = {}
        self._dependsOn_adjacency = {}

        self._linking_predicates_adjacency = {}

        # Get logger (only used for the constructor)
        logger = logging.getLogger()

        # Querying owl:sameAs edges
        logger.info("Querying owl:sameAs edges")
        edges = server_manager.query_two_elements("?e1 owl:sameAs ?e2 . ", verbose=True)

        logger.info("Processing owl:sameAs edges")
        for e in tqdm.tqdm(edges):
            n1 = self._cache_manager.get_element_index(e[0])
            if n1 not in self._sameas_adjacency:
                self._sameas_adjacency[n1] = set()

            n2 = self._cache_manager.get_element_index(e[1])
            if n2 not in self._sameas_adjacency:
                self._sameas_adjacency[n2] = set()

            self._sameas_adjacency[n1].add(n2)

        # Completing edges
        logger.info("Completing owl:sameAs edges with symmetry")
        for node_index in tqdm.tqdm(self._sameas_adjacency):
            for neighbor in self._sameas_adjacency[node_index]:
                if node_index not in self._sameas_adjacency[neighbor]:
                    self._sameas_adjacency[neighbor].add(node_index)

        logger.info("Completing owl:sameAs edges with transitivity")
        to_compute = set(self._sameas_adjacency.keys())
        with tqdm.tqdm(total=len(to_compute)) as pbar:
            while len(to_compute) != 0:
                current_node = to_compute.pop()
                connected_component = self._compute_sameas_connected_component(current_node)

                for n in connected_component:
                    self._sameas_adjacency[n] = connected_component.difference({n})
                    to_compute -= {n}
                    pbar.update(1)

        # Querying rdfs:subClassOf edges
        logger.info("Querying rdfs:subClassOf edges")
        edges = server_manager.query_two_elements("?e1 rdfs:subClassOf ?e2 . ", verbose=True)

        logger.info("Processing rdfs:subClassOf edges")
        for e in tqdm.tqdm(edges):
            n1 = self._cache_manager.get_element_index(e[0])
            if n1 not in self._subclassof_adjacency:
                self._subclassof_adjacency[n1] = set()

            n2 = self._cache_manager.get_element_index(e[1])
            if n2 not in self._subclassof_adjacency:
                self._subclassof_adjacency[n2] = set()

            self._subclassof_adjacency[n1].add(n2)

        # Querying rdf:type edges
        logger.info("Querying rdf:type edges")
        edges = server_manager.query_two_elements("?e1 rdf:type ?e2 . ", verbose=True)

        logger.info("Processing rdf:type edges")
        for e in tqdm.tqdm(edges):
            n1 = self._cache_manager.get_element_index(e[0])
            if n1 not in self._type_adjacency:
                self._type_adjacency[n1] = set()

            n2 = self._cache_manager.get_element_index(e[1])
            if n2 not in self._type_adjacency:
                self._type_adjacency[n2] = set()

            self._type_adjacency[n1].add(n2)

        # Expanding rdf:type edges with owl:sameAs and rdfs:subClassOf links
        logger.info("Expanding rdf:type edges with owl:sameAs and rdfs:subClassOf links")
        to_compute = set(self._type_adjacency.keys())
        with tqdm.tqdm(total=len(to_compute)) as pbar:
            while len(to_compute) != 0:
                current_node = to_compute.pop()

                type_expansion = self._type_adjacency[current_node]

                # Expansion with sameAs nodes
                if current_node in self._sameas_adjacency:
                    for same_node in self._sameas_adjacency[current_node]:
                        if same_node in self._type_adjacency:
                            type_expansion |= self._type_adjacency[same_node]

                # Expansion with rdfs:subClassOf and sameAs nodes in type_expansion
                type_expansion = self.get_nodes_sameas_subclassof_expansion(type_expansion)

                # Type affectation for each node (current_node and sameAs nodes)
                self._type_adjacency[current_node] = type_expansion
                pbar.update(1)

                if current_node in self._sameas_adjacency:
                    for same_node in self._sameas_adjacency[current_node]:
                        if same_node in self._type_adjacency:
                            to_compute -= {same_node}
                            pbar.update(1)

                        self._type_adjacency[same_node] = type_expansion

        # Querying partOf edges
        logger.info("Building partOf adjacency")
        for part_of_predicate in part_of_predicates:
            logger.info("Querying %s edges" % part_of_predicate)
            edges = server_manager.query_two_elements("?e1 <%s> ?e2 . " % part_of_predicate, verbose=True)

            logger.info("Processing %s edges" % part_of_predicate)
            for e in tqdm.tqdm(edges):
                n1 = self._cache_manager.get_element_index(e[0])
                if n1 not in self._partOf_adjacency:
                    self._partOf_adjacency[n1] = set()

                n2 = self._cache_manager.get_element_index(e[1])
                if n2 not in self._partOf_adjacency:
                    self._partOf_adjacency[n2] = set()

                self._partOf_adjacency[n1].add(n2)

        # Querying hasPart edges
        logger.info("Completing partOf adjacency with hasPart edges")
        for has_part_predicate in has_part_predicates:
            logger.info("Querying %s edges" % has_part_predicate)
            edges = server_manager.query_two_elements("?e1 <%s> ?e2 . " % has_part_predicate, verbose=True)

            logger.info("Processing %s edges" % has_part_predicate)
            for e in tqdm.tqdm(edges):
                n1 = self._cache_manager.get_element_index(e[0])
                if n1 not in self._partOf_adjacency:
                    self._partOf_adjacency[n1] = set()

                n2 = self._cache_manager.get_element_index(e[1])
                if n2 not in self._partOf_adjacency:
                    self._partOf_adjacency[n2] = set()

                # We add n2 -> n1 in partOf adjacency as hasPart is the inverse of partOf
                self._partOf_adjacency[n2].add(n1)

        # Querying dependsOn edges
        logger.info("Building dependsOn adjacency")
        for depends_on_predicate in depends_on_predicates:
            logging.info("Querying %s edges" % depends_on_predicate)
            edges = server_manager.query_two_elements("?e1 <%s> ?e2 . " % depends_on_predicate, verbose=True)

            logger.info("Processing %s edges" % depends_on_predicate)
            for e in tqdm.tqdm(edges):
                n1 = self._cache_manager.get_element_index(e[0])
                if n1 not in self._dependsOn_adjacency:
                    self._dependsOn_adjacency[n1] = set()

                n2 = self._cache_manager.get_element_index(e[1])
                if n2 not in self._dependsOn_adjacency:
                    self._dependsOn_adjacency[n2] = set()

                self._dependsOn_adjacency[n1].add(n2)

        # Querying entities linked by linking predicates
        for lp in integration_ontology.get_linking_predicates():
            logger.info("Querying linking predicate %s edges" % lp)
            edges = server_manager.query_two_elements("?e1 <%s> ?e2 . " % lp, verbose=True)

            self._linking_predicates_adjacency[lp] = {}
            if len(edges) != 0:
                logger.info("Processing linking predicate %s edges" % lp)
                for e in tqdm.tqdm(edges):
                    n1 = self._cache_manager.get_element_index(e[0])
                    if n1 not in self._linking_predicates_adjacency[lp]:
                        self._linking_predicates_adjacency[lp][n1] = set()

                    n2 = self._cache_manager.get_element_index(e[1])
                    if n2 not in self._linking_predicates_adjacency[lp]:
                        self._linking_predicates_adjacency[lp][n2] = set()

                    self._linking_predicates_adjacency[lp][n1].add(n2)
            else:
                logger.info("No edge found")

        # Completing linking predicates adjacencies with inverses
        logger.info("Completing linking predicates adjacencies with inverses")
        for lp in tqdm.tqdm(integration_ontology.get_linking_predicates()):
            for lpi in integration_ontology.get_linking_predicate_inverses(lp):
                for n in self._linking_predicates_adjacency[lp]:
                    for n2 in self._linking_predicates_adjacency[lp][n]:
                        if n2 not in self._linking_predicates_adjacency[lpi]:
                            self._linking_predicates_adjacency[lpi][n2] = set()

                        self._linking_predicates_adjacency[lpi][n2].add(n)

        # Expanding linking predicates adjacencies following hierarchy
        logger.info("Expanding linking predicates adjacencies following hierarchy")
        for lp in tqdm.tqdm(integration_ontology.get_linking_predicates()):
            ancestors = integration_ontology.get_linking_predicate_ancestors(lp)

            for a in ancestors:
                for n in self._linking_predicates_adjacency[lp]:
                    if n not in self._linking_predicates_adjacency[a]:
                        self._linking_predicates_adjacency[a][n] = set(self._linking_predicates_adjacency[lp][n])

                    else:
                        self._linking_predicates_adjacency[a][n] |= set(self._linking_predicates_adjacency[lp][n])

    def _compute_sameas_connected_component(self, current_node_index):
        """
        Computes the sameAs connected component the current_node_index belongs to
        :param current_node_index: the seed node index for the connected component computation
        :return: the set of nodes indices forming the connected component the current_node_index belongs to
        (including itself)
        """

        connected_component = {current_node_index}
        q = queue.Queue()
        q.put(current_node_index)

        while not q.empty():
            n = q.get()

            for n2 in self._sameas_adjacency[n]:
                if n2 not in connected_component:
                    connected_component.add(n2)
                    q.put(n2)

        return connected_component

    def get_node_sameas_adjacency(self, node_index):
        """
        Returns the set of nodes indices that are same as the given node_index
        :param node_index:
        :return: the set of nodes indices that are same as the given node_index
        """
        if node_index not in self._sameas_adjacency:
            return set()

        return set(self._sameas_adjacency[node_index])

    def get_nodes_sameas_subclassof_expansion(self, nodes_indices):
        """
        Returns the expansion of nodes_indices following owl:sameAs and rdfs:subClassOf links
        :param nodes_indices: seed nodes indices for the expansion
        :return: Returns all nodes connected via sameAs/subClassOf links with the nodes_indices nodes including the
        seed nodes
        """

        retval = set(nodes_indices)
        diff = set(nodes_indices)

        while len(diff) != 0:
            temp = set(retval)

            for n in diff:
                if n in self._sameas_adjacency:
                    temp |= self._sameas_adjacency[n]

                if n in self._subclassof_adjacency:
                    temp |= self._subclassof_adjacency[n]

            diff = temp - retval
            retval = temp

        return retval

    def get_nodes_typed_by(self, class_uri):
        """
        Returns the nodes indices that have the class_uri in their type adjacency
        :param class_uri: the class URI to be found in type adjacency
        :return: the set of of nodes indices that have the class_uri in their type adjacency
        """

        class_uri_index = self._cache_manager.get_element_index(class_uri)

        retval = set()

        for n in self._type_adjacency:
            if class_uri_index in self._type_adjacency[n]:
                retval.add(n)

        return retval

    def get_node_linking_predicate_adjacency_typed_by(self, node_index, linking_predicate, class_uri):
        """
        Returns all nodes indices n such that node_index -- linking_predicate --> n and n is typed by class_uri.
        owl:sameAs links are not considered on the seed node or the returned nodes
        :param node_index: the initial seed node index
        :param linking_predicate: URI of the linking predicate used to connect the node_index with the returned nodes
        :param class_uri: URI of the class to be instantiated by returned nodes
        :return: set of all nodes n such that node_index -- linking_predicate --> n and n is typed by class_uri
        """

        class_uri_index = self._cache_manager.get_element_index(class_uri)

        retval = set()

        if node_index in self._linking_predicates_adjacency[linking_predicate]:
            for n in self._linking_predicates_adjacency[linking_predicate][node_index]:
                if n in self._type_adjacency and class_uri_index in self._type_adjacency[n]:
                    retval.add(n)

        return retval

    def get_part_of_links(self):
        """
        Returns a set of tuple (n_index_1, n_index_2) of nodes indices having a partOf adjacency
        :return: set of tuple (n_index_1, n_index_2) of nodes indices having a partOf adjacency
        """

        retval = set()

        for n1 in self._partOf_adjacency:
            for n2 in self._partOf_adjacency[n1]:
                retval.add((n1, n2))

        return retval

    def get_depends_on_links(self):
        """
        Returns a set of tuple (n_index_1, n_index_2) of nodes indices having a dependsOn adjacency
        :return: set of tuple (n_index_1, n_index_2) of nodes indices having a dependsOn adjacency
        """

        retval = set()

        for n1 in self._dependsOn_adjacency:
            for n2 in self._dependsOn_adjacency[n1]:
                retval.add((n1, n2))

        return retval

    def get_type_adjacency(self, node_index):
        """
        Returns the set of nodes indices being instantiated by the given node_index
        :param node_index: the node index whose type adjacency is needed
        :return: set of nodes indices being instantiated by the given node_index
        """

        if node_index not in self._type_adjacency:
            return set()

        return set(self._type_adjacency[node_index])
