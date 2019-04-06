import logging

import tqdm

from core.io.QueryElementsThread import QueryElementsThread

__author__ = "Pierre Monnin"


class DimensionOntology:
    """
    Class representing an ontology used in the preorder of one dimension
    """

    class OntologyClass:
        """
        Class representing a class of a DimensionOntology
        """

        def __init__(self, uris_indices):
            """
            Builds the OntologyClass
            :param uris_indices: the set of URIs indices corresponding to the class
            """

            self._uris_indices = uris_indices
            self._ancestors = set()
            self._descendants = set()

        def get_uris_indices(self):
            """
            Returns the set of URIs indices corresponding to the class
            :return: set of URIs indices corresponding to the class
            """

            return set(self._uris_indices)

        def add_ancestor(self, ancestor_index):
            """
            Adds an ancestor to the current ontology class
            :param ancestor_index: the ontology class index of the ancestor to add
            """
            self._ancestors.add(ancestor_index)

        def add_descendant(self, descendant_index):
            """
            Adds a descendant to the current ontology class
            :param descendant_index: the ontology class index of the descendant to add
            """
            self._descendants.add(descendant_index)

        def get_ancestors(self):
            """
            Returns the set of ontology classes indices that are ancestors of the current ontology class
            :return: set of ontology classes indices that are ancestors of the current ontology class
            """

            return set(self._ancestors)

        def get_descendants(self):
            """
            Returns the set of ontology classes indices that are descendants of the current ontology class
            :return: set of ontology classes indices that are descendants of the current ontology class
            """

            return set(self._descendants)

        def __str__(self):
            retval = "Ontology class [" + \
                     "uris_indices:" + str(self._uris_indices) + \
                     "; ancestors: " + str(self._ancestors) + \
                     "; descendants: " + str(self._descendants) + "]"
            return retval

    def __init__(self, base_uris, configuration_parameters, max_rows, nb_threads, cache_manager, rdf_graph):
        """
        Builds the DimensionOntology
        :param base_uris: base URIs to be considered to build the DimensionOntology (list of strings)
        :param configuration_parameters: configuration parameters of the scripts
        :param max_rows: max rows that can be queried from the triplestore
        :param nb_threads: number of threads that can be used
        :param cache_manager: global cache manager for the scripts (URI <-> node index in the graph)
        :param rdf_graph: the RDF Graph model
        """

        logger = logging.getLogger()

        # Cache manager is used to have a mapping URI <-> node index for every node in the graph
        self._cache_manager = cache_manager
        # Classes indices are classes grouped by owl:sameAs connected components, they may correspond to multiple nodes
        self._cache_index_to_class_index = {}
        self._classes = []

        self._base_uris = set(base_uris)

        if len(base_uris) != 0:
            # Querying classes
            logger.info("Querying classes")

            queries = [
                """
                    ?e rdf:type owl:Class .
                    FILTER(REGEX(STR(?e), "%s", "i")) .
                """,
                """
                    ?s rdf:type ?e .
                    FILTER(REGEX(STR(?e), "%s", "i")) .
                """,
                """
                   ?s rdfs:subClassOf ?e .
                    FILTER(REGEX(STR(?e), "%s", "i")) . 
                """,
                """
                    ?e rdfs:subClassOf ?s .
                    FILTER(REGEX(STR(?e), "%s", "i")) .
                """
            ]

            # Thread creation
            threads = []
            for base_uri in base_uris:
                for query in queries:
                    threads.append(QueryElementsThread(configuration_parameters, max_rows, query % base_uri))

            # Thread running and joining
            i = 0
            results = set()
            with tqdm.tqdm(total=len(threads)) as pbar:
                while i < len(threads):
                    for j in range(0, min(nb_threads, len(threads) - i)):
                        threads[i + j].start()

                    for j in range(0, min(nb_threads, len(threads) - i)):
                        threads[i + j].join()
                        results |= threads[i + j].get_results()

                    pbar.update(min(nb_threads, len(threads) - i))
                    i += min(nb_threads, len(threads) - i)

            del threads

            # owl:sameAs reduction
            logger.info("owl:sameAs reduction")
            for class_uri in tqdm.tqdm(results):
                class_cache_index = self._cache_manager.get_element_index(class_uri)

                if class_cache_index not in self._cache_index_to_class_index:
                    classes_cache_indices = {class_cache_index}

                    # Consider all the URIs that can be part of the OntologyClass (from sameAs expansion)
                    for same_class_cache_index in rdf_graph.get_node_sameas_adjacency(class_cache_index):
                        # Keep indices that are in the base_uris namespaces
                        if not self._exclude_class(self._cache_manager.get_element_from_index(same_class_cache_index)):
                            classes_cache_indices.add(same_class_cache_index)

                    ontology_class = DimensionOntology.OntologyClass(classes_cache_indices)
                    for i in classes_cache_indices:
                        self._cache_index_to_class_index[i] = len(self._classes)

                    self._classes.append(ontology_class)

            # subClassOf relationships
            logger.info("Ancestors / descendants computation")
            for i, ontology_class in enumerate(tqdm.tqdm(self._classes)):
                expansion = rdf_graph.get_nodes_sameas_subclassof_expansion(ontology_class.get_uris_indices())

                for n in expansion:
                    # Exclude classes that are not from the base_uris namespaces and self classes
                    if not self._exclude_class(self._cache_manager.get_element_from_index(n)):
                        ancestor_class_index = self._cache_index_to_class_index[n]

                        if ancestor_class_index != i:
                            ontology_class.add_ancestor(ancestor_class_index)
                            self._classes[ancestor_class_index].add_descendant(i)

    def get_classes_indices_from_uris_indices(self, uris_indices):
        """
        Returns classes indices from URIs indices (nodes indices in the CacheManager)
        :param uris_indices: URIs indices (nodes indices in the CacheManager)
        :return: set of classes indices corresponding to the given URIs indices
        """

        classes_indices = set()

        for i in uris_indices:
            if i in self._cache_index_to_class_index:
                classes_indices.add(self._cache_index_to_class_index[i])

        return classes_indices

    def min(self, classes_indices):
        """
        Returns the set of minimum classes indices from the given set of class indices. The min is computed as follows
        min(classes_indices) = {Ci | not exists Di in classes_indices such as Di <= Ci}
        :param classes_indices: the set of classes indices whose minimum is needed
        :return: min(classes_indices) = {Ci | not exists Di in classes_indices such as Di != Ci and Di <= Ci}
        """

        retval = set()

        for c in classes_indices:
            if not any(c in self._classes[d].get_ancestors() for d in classes_indices - {c}):
                retval.add(c)

        return retval

    def is_subsumed(self, c1, c2):
        """
        Returns true if c1 <= c2
        :param c1: class index 1
        :param c2: class index 2
        :return: tue if c1 <= c2
        """

        return c1 == c2 or c2 in self._classes[c1].get_ancestors()

    def get_base_uris(self):
        """
        Returns the DimensionOntology base URIs namespaces
        :return: DimensionOntology base URIs namespaces
        """

        return set(self._base_uris)

    def _exclude_class(self, class_uri):
        """
        Returns true if the class URI should be exluded from the current DimensionOntology (not in the namespace)
        :param class_uri: class URI to check if belonging to the namespace of the current DimensionOntology
        :return: true if the class URIs should be exluded from the current DimensionOntology (not in the namespace)
        """

        for base_uri in self._base_uris:
            if class_uri.startswith(base_uri):
                return False

        return True

    def __str__(self):
        retval = "-- DimensionOntology --\n"

        for c in self._classes:
            retval += str(c) + "\n"

        retval += "----"

        return retval

    def __hash__(self):
        return hash("".join(self._base_uris))

    def __eq__(self, other):
        return self._base_uris == other.get_base_uris()
