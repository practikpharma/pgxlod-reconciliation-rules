import itertools
import logging
import tqdm

from core.reconciliation.preorders import OrderResult, PartOfPreorder, MsciPreorder

__author__ = "Pierre Monnin"


class RelationshipElement:
    """
    Defines an element appearing in a dimension of a Relationship. Such an element is a node (*) in the RDF Graph
    linked at least once with a linking predicate to a node representing a Relationship.
    (*) or a set of nodes that are owl:sameAs
    """

    def __init__(self, element_index, uris_indices):
        """
        Builds a RelationshipElement, with the index element_index and representing the set of uris_indices in the RDF
        Graph
        :param element_index: index of the RelationshipElement in the Relationships model
        :param uris_indices: index of the URIs in the RDFGraph that are represented by the RelationshipElement
        """

        self._element_index = element_index
        self._uris_indices = uris_indices

        # partOf and dependsOn adjacencies contain the indices of the RelationshipElements that are adjacent
        self._part_of_adjacency = set()
        self._depends_on_adjacency = set()

        # Dictionaries whose keys are DimensionOntologies and values are sets of classes indices from these ontologies
        self._classes_instantiated = {}
        self._msci = {}

    def get_element_index(self):
        """
        Returns the RelationshipElement index in the Relationships model
        :return: the RelationshipElement index in the Relationships model
        """

        return self._element_index

    def get_uris_indices(self):
        """
        Returns the set of URIs indices that are represented by the RelationshipElement
        :return: set of URIs indices that are represented by the RelationshipElement
        """

        return set(self._uris_indices)

    def add_part_of_adjacency(self, element_index):
        """
        Adds the element_index in the partOf adjacency of the current RelationshipElement
        :param element_index: index of a RelationshipElement such as partOf(current, element)
        """

        self._part_of_adjacency.add(element_index)

    def add_depends_on_adjacency(self, element_index):
        """
        Adds the element_index in the partOf adjacency of the current RelationshipElement
        :param element_index: index of a RelationshipElement such as partOf(current, element)
        """
        self._depends_on_adjacency.add(element_index)

    def set_classes_instantiated(self, dimension_ontology, classes_indices):
        """
        Defines the set of classes instantiated by the RelationshipElement w.r.t. the dimension ontology
        :param dimension_ontology: dimension ontology whose classes belongs to
        :param classes_indices: indices of classes from the DimensionOntology that the RelationshipElement instantiates
        """

        self._classes_instantiated[dimension_ontology] = set(classes_indices)
        self._msci[dimension_ontology] = dimension_ontology.min(classes_indices)

    def get_classes_instantiated(self, dimension_ontology):
        """
        Returns the set of indices of classes from the DimensionOntology that the RelationshipElement instantiates
        :param dimension_ontology: the DimensionOntology whose classes are considered
        :return: set of indices of classes from the DimensionOntology that the RelationshipElement instantiates
        """

        if dimension_ontology not in self._classes_instantiated:
            return set()

        return set(self._classes_instantiated[dimension_ontology])

    def get_depends_on_adjacency(self):
        """
        Returns the set of indices of RelationshipElements that are adjacent via dependsOn with the current element
        :return: set of indices of RelationshipElements that are adjacent via dependsOn with the current element
        """

        return set(self._depends_on_adjacency)

    def is_part_of(self, element):
        """
        Returns true if the current RelationshipElement is part of the given element
        :param element: a RelationshipElement (not an index)
        :return: true if the current RelationshipElement is part of the given element
        """

        return element.get_element_index() in self._part_of_adjacency

    def msci(self, dimension_ontology):
        """
        Returns the minimum classes of dimension_ontology instantiated by the current RelationshipElement
        :param dimension_ontology: the DimensionOntology to consider
        :return: Returns the minimum classes of dimension_ontology instantiated by the current RelationshipElement
        """

        if dimension_ontology not in self._msci:
            return set()

        return set(self._msci[dimension_ontology])

    def __str__(self):
        retval = "RelationshipElement [element_index: " + str(self._element_index) + \
               "; uris_indices: " + str(self._uris_indices) + \
               "; partOf: " + str(self._part_of_adjacency) + \
               "; dependsOn: " + str(self._depends_on_adjacency)

        for dimension_ontology in self._classes_instantiated:
            retval += "; " + str(dimension_ontology.get_base_uris()) + ": " + \
                      str(self._classes_instantiated[dimension_ontology])

        retval += " ]"
        return retval


class Relationship:
    """
    Defines a Relationship, that appears as a node in the RDF Graph
    """

    def __init__(self, uri_index):
        """
        Builds the Relationship
        :param uri_index: the index of the URI representing the Relationship in the RDFGraph
        """

        self._uri_index = uri_index
        self._dimensions = {}

    def get_uri_index(self):
        """
        Returns the URI index of the Relationship
        :return: the URI index of the Relationship
        """

        return self._uri_index

    def add_dimension(self, dimension_name, linking_predicate, elements_indices):
        """
        Adds a dimension to the Relationship
        :param dimension_name: name of the dimension
        :param linking_predicate: linking predicate used to link RelationshipElements
        :param elements_indices: indices of the RelationshipElements in the dimension dimension_name / linking predicate
        """

        if dimension_name not in self._dimensions:
            self._dimensions[dimension_name] = {}

        self._dimensions[dimension_name][linking_predicate] = set(elements_indices)

    def get_dimension(self, dimension_name, linking_predicate):
        """
        Returns the set of RelationshipElements indices that are in the dimension dimension_name/linking predicate
        :param dimension_name: dimension name defining the dimension
        :param linking_predicate: linking predicate used to link RelationshipElements to the Relationship
        :return: set of RelationshipElements indices that are in the dimension dimension_name/linking predicate
        """

        if dimension_name in self._dimensions and linking_predicate in self._dimensions[dimension_name]:
            return set(self._dimensions[dimension_name][linking_predicate])

        return set()

    def __str__(self):
        retval = "-- Relationship (node index: " + str(self._uri_index) + ") --\n"
        for dimension_name in self._dimensions:
            for lp in self._dimensions[dimension_name]:
                if len(self._dimensions[dimension_name][lp]) != 0:
                    retval += dimension_name + " / " + lp + ": " + str(self._dimensions[dimension_name][lp]) + "\n"

        return retval


class RelationshipsModel:
    """
    Main class to use for the reconciliation of relationship. Represents the global model for the reconciliation.
    """

    def __init__(self, rdf_graph, integration_ontology, dimensions_ontologies, configuration_parameters, cache_manager):
        """
        Builds the Relationships Model
        :param rdf_graph: the RDFGraph used for the reconciliation
        :param integration_ontology: the integration ontology used to represent the relationship
        :param dimensions_ontologies: the dimensions ontologies used for each dimension
        :param configuration_parameters: the configuration parameters of the scripts
        :param cache_manager: the global cache manager of the scripts (URI <-> node index in the graph)
        """

        self._logger = logging.getLogger()

        # Cache manager is used to have a mapping URI <-> cache index for every node in the graph
        # Elements indices are elements grouped by sameAs connected components and can correspond to several nodes
        self._cache_manager = cache_manager
        self._cache_index_to_elements_index = {}
        self._elements = []

        self._integration_ontology = integration_ontology

        self._dimensions = configuration_parameters["dimensions"]
        self._do_related_enabled = any(d["depends-on-similarity"] for d in self._dimensions)
        self._relationships = {}

        # Build preorders
        self._preorders = {}
        for d in self._dimensions:
            if d["preorder"] == "PartOfPreorder":
                self._preorders[d["name"]] = PartOfPreorder()

            else:
                self._preorders[d["name"]] = MsciPreorder(dimensions_ontologies[d["name"]])

        # Getting all relationships
        self._logger.info("Building relationships and their components")
        for relationship_class_uri in configuration_parameters["integration-ontology-relationships-classes"]:
            self._logger.info("Getting relationships instantiating %s" % relationship_class_uri)

            for rel_index in tqdm.tqdm(rdf_graph.get_nodes_typed_by(relationship_class_uri)):
                if rel_index not in self._relationships:
                    relationship = Relationship(rel_index)

                    for dimension in configuration_parameters["dimensions"]:
                        lp_dimension = integration_ontology.linking_predicates_descendants_expansion(
                            dimension["integration-ontology-top-linking-predicates"]
                        )

                        # We build a dimension of a relationship for each pair dimension / linking predicate
                        for lp in lp_dimension:
                            dim_lp_elements = set()

                            # Get nodes indices n such that rel_index -- linking predicate --> n and dim_class(n)
                            for dim_class in dimension["integration-ontology-top-classes"]:
                                for n in rdf_graph.get_node_linking_predicate_adjacency_typed_by(rel_index, lp,
                                                                                                 dim_class):
                                    # We add the element to the dimension
                                    dim_lp_elements.add(self._get_element_index_from_cache_index(n, rdf_graph))

                            # We add the dimension to the relationship
                            relationship.add_dimension(dimension["name"], lp, dim_lp_elements)

                    self._relationships[rel_index] = relationship

        # Building partOf links
        self._logger.info("Building partOf links")
        for (node_index_1, node_index_2) in tqdm.tqdm(rdf_graph.get_part_of_links()):
            element_index_1 = self._get_element_index_from_cache_index(node_index_1, rdf_graph)
            element_index_2 = self._get_element_index_from_cache_index(node_index_2, rdf_graph)

            self._elements[element_index_1].add_part_of_adjacency(element_index_2)

        # Building dependsOn links
        self._logger.info("Building dependsOn links")
        for (node_index_1, node_index_2) in tqdm.tqdm(rdf_graph.get_depends_on_links()):
            element_index_1 = self._get_element_index_from_cache_index(node_index_1, rdf_graph)
            element_index_2 = self._get_element_index_from_cache_index(node_index_2, rdf_graph)

            self._elements[element_index_1].add_depends_on_adjacency(element_index_2)

        # Building relationships elements types
        self._logger.info("Building relationships elements types")
        for element in tqdm.tqdm(self._elements):
            # We can only use one URI from the elements URIs as type adjacency in RDF graph has been expanded
            element_type = rdf_graph.get_type_adjacency(element.get_uris_indices().pop())

            for dimension in configuration_parameters["dimensions"]:
                dimension_ontology = dimensions_ontologies[dimension["name"]]
                element.set_classes_instantiated(
                    dimension_ontology,
                    dimension_ontology.get_classes_indices_from_uris_indices(element_type)
                )

    def _get_element_index_from_cache_index(self, node_index, rdf_graph):
        """
        Returns the RelationshipElement index of an URI index. If the RelationshipElement does not exist, it is created
        taking into account owl:sameAs nodes
        :param node_index: the URI index
        :param rdf_graph: the RDFGraph model
        :return: the element index corresponding to the URI index
        """

        # If node_index is not already mapped to an element, we create the element for it (and all its sameAs URIs)
        if node_index not in self._cache_index_to_elements_index:
            sameas_nodes = rdf_graph.get_node_sameas_adjacency(node_index)
            element = RelationshipElement(len(self._elements), sameas_nodes.union({node_index}))

            self._cache_index_to_elements_index[node_index] = len(self._elements)
            for sameas_node in sameas_nodes:
                self._cache_index_to_elements_index[sameas_node] = len(self._elements)

            self._elements.append(element)

        return self._cache_index_to_elements_index[node_index]

    def reconcile(self):
        """
        Reconcile all relationships in the RelationshipsModel
        :return: A list of dictionaries (uri_index_1, order_result, uri_index_2) where order_result is either
        OrderResult.EQUAL, EQUIV, LEQ, or GEQ. It can also be DO_RELATED if the dependsOn similarity is enabled for
        at least one dimension. INCOMPARABLE relationships are discarded
        """
        reconciliation_results = []

        with tqdm.tqdm(total=len(self._relationships) * (len(self._relationships) - 1) // 2) as pbar:
            for rel1, rel2 in itertools.combinations(self._relationships.values(), 2):
                result = self.compare(rel1, rel2)

                if result != OrderResult.INCOMPARABLE:
                    reconciliation_results.append({
                        "uri_index_1": rel1.get_uri_index(),
                        "order_result": result,
                        "uri_index_2": rel2.get_uri_index()
                    })
                pbar.update(1)

        return reconciliation_results

    def explain_reconciliation(self, rel_node_1, rel_node_2):
        """
        Explain the reconciliation results between two relationships from their node indices
        :param rel_node_1: node index of the first relationship
        :param rel_node_2: node index of the second relationship
        """

        if rel_node_1 not in self._relationships:
            self._logger.critical("Relationship 1 is not in RelationshipsModel")

        elif rel_node_2 not in self._relationships:
            self._logger.critical("Relationship 2 is not in RelationshipsModel")

        else:
            self.compare_verbose(self._relationships[rel_node_1], self._relationships[rel_node_2])

    def compare(self, rel1, rel2):
        """
        Compare two relationships
        :param rel1: First relationship (object)
        :param rel2: Second relationship (object)
        :return: Either OrderResult.EQUAL, EQUIV, LEQ, GEQ, DO_RELATED (if enabled) or INCOMPARABLE
        """

        compare_result = OrderResult.EQUAL

        # Rules 1, 2 and 3
        dimensions_to_explore = list(self._dimensions)
        while compare_result != OrderResult.INCOMPARABLE and len(dimensions_to_explore) != 0:
            dimension = dimensions_to_explore.pop()
            lp_dimension = self._integration_ontology.linking_predicates_descendants_expansion(
                dimension["integration-ontology-top-linking-predicates"]
            )

            while compare_result != OrderResult.INCOMPARABLE and len(lp_dimension) != 0:
                lp = lp_dimension.pop()

                preorder_result = self._preorders[dimension["name"]].compare(
                    {self._elements[i] for i in rel1.get_dimension(dimension["name"], lp)},
                    {self._elements[i] for i in rel2.get_dimension(dimension["name"], lp)}
                )

                compare_result &= preorder_result

        # Test Rule 4 if and only if all previous rules have failed and one dimension enables DO relatedness
        if self._do_related_enabled and compare_result == OrderResult.INCOMPARABLE:
            for dimension in self._dimensions:
                if dimension["depends-on-similarity"]:
                    if self._is_one_other_dimension_nonempty_equivalent(rel1, rel2, dimension):
                        if self._is_depends_on_equivalent(rel1, rel2, dimension) or \
                                self._is_depends_on_equivalent(rel2, rel1, dimension):
                            compare_result = OrderResult.DO_RELATED

        return compare_result

    def compare_verbose(self, rel1, rel2):
        """
        Compare two relationships displaying result for each dimension
        :param rel1: First relationship (object)
        :param rel2: Second relationship (object)
        :return: Either OrderResult.EQUAL, EQUIV, LEQ, GEQ, DO_RELATED (if enabled) or INCOMPARABLE
        """

        compare_result = OrderResult.EQUAL

        # Rules 1, 2 and 3
        for dimension in self._dimensions:
            lp_dimension = self._integration_ontology.linking_predicates_descendants_expansion(
                dimension["integration-ontology-top-linking-predicates"]
            )

            for lp in lp_dimension:
                preorder_result = self._preorders[dimension["name"]].compare(
                    {self._elements[i] for i in rel1.get_dimension(dimension["name"], lp)},
                    {self._elements[i] for i in rel2.get_dimension(dimension["name"], lp)}
                )

                self._logger.info(dimension["name"] + " / " + lp + " => " + str(preorder_result))

                compare_result &= preorder_result

        # Test Rule 4 if and only if all previous rules have failed and one dimension enables DO relatedness
        if self._do_related_enabled and compare_result == OrderResult.INCOMPARABLE:
            for dimension in self._dimensions:
                if dimension["depends-on-similarity"]:
                    if self._is_one_other_dimension_nonempty_equivalent(rel1, rel2, dimension):
                        if self._is_depends_on_equivalent(rel1, rel2, dimension) or \
                                self._is_depends_on_equivalent(rel2, rel1, dimension):
                            compare_result = OrderResult.DO_RELATED

        self._logger.info("Final result: " + str(compare_result))

        return compare_result

    def _is_one_other_dimension_nonempty_equivalent(self, rel1, rel2, excluded_dimension):
        """
        Returns true if one dimension in rel1 and rel2 is non-empty for at least one linking predicate of the dimension
        and equivalent for all linking predicate of the dimension. Only tests dimensions that are not equal to
        the given excluded dimension.
        :param rel1: a Relationship
        :param rel2: a Relationship
        :param excluded_dimension: dimension not to be tested
        :return: true if one dimension in rel1 and rel2 is non-empty for at least one linking predicate of the dimension
        and equivalent for all linking predicate of the dimension
        """

        for dimension in self._dimensions:
            if dimension != excluded_dimension:
                if self._is_non_empty_dimension(rel1, dimension):
                    if self._all_equivalent_for_dimension(rel1, rel2, dimension):
                        return True

        return False

    def _is_non_empty_dimension(self, relationship, dimension):
        """
        Returns true if the dimension is non-empty in the relationship for at least one linking predicate of the
        dimension
        :param relationship: the relationship to check
        :param dimension: the dimension to check
        :return: true if the dimension is non-empty in the relationship for at least one linking predicate of the
        dimension
        """

        lp_dimension = self._integration_ontology.linking_predicates_descendants_expansion(
            dimension["integration-ontology-top-linking-predicates"]
        )

        return any(len(relationship.get_dimension(dimension["name"], lp)) != 0 for lp in lp_dimension)

    def _all_equivalent_for_dimension(self, rel1, rel2, dimension):
        """
        Returns true if all pair dimension / linking predicate are equivalent for rel1 and rel2 and the given dimension
        :param rel1: a Relationship
        :param rel2: a Relationship
        :param dimension: the dimension to check
        :return: true if all pair dimension / linking predicate are equivalent for rel1 and rel2 and the given dimension
        """

        lp_dimension = self._integration_ontology.linking_predicates_descendants_expansion(
            dimension["integration-ontology-top-linking-predicates"]
        )

        return all(self._preorders[dimension["name"]].compare(
            {self._elements[i] for i in rel1.get_dimension(dimension["name"], lp)},
            {self._elements[i] for i in rel2.get_dimension(dimension["name"], lp)}
        ) & OrderResult.EQUIVALENT == OrderResult.EQUIVALENT for lp in lp_dimension)

    def _is_depends_on_equivalent(self, rel1, rel2, do_dimension):
        """
        Tests if the set of elements linked by dependsOn to the do_dimension of rel1 are equivalent to another
        dimension of rel2 or to the set of elements linked by dependsOn to the do_dimension of rel2
        :param rel1: a Relationship
        :param rel2: a Relationship
        :param do_dimension: the dimension on which the dependsOn similarity is tested
        :return: true if the set of elements linked by dependsOn to the do_dimension of rel1 are equivalent to another
        dimension of rel2 or to the set of elements linked by dependsOn to the do_dimension of rel2
        """

        lp_do_dimension = self._integration_ontology.linking_predicates_descendants_expansion(
            do_dimension["integration-ontology-top-linking-predicates"]
        )

        for other_dimension in self._dimensions:
            lp_other_dimension = self._integration_ontology.linking_predicates_descendants_expansion(
                other_dimension["integration-ontology-top-linking-predicates"]
            )

            if other_dimension == do_dimension:
                if any(
                        len(self._depends_on_union(rel1.get_dimension(do_dimension["name"], p1))) != 0
                        and
                        self._depends_on_union(rel1.get_dimension(do_dimension["name"], p1))
                        ==
                        self._depends_on_union(rel2.get_dimension(other_dimension["name"], p1))
                        for p1 in lp_do_dimension
                ):
                    return True

            else:
                if any(
                        len(self._depends_on_union(rel1.get_dimension(do_dimension["name"], p1))) != 0
                        and
                        self._preorders[other_dimension["name"]].compare(
                            {
                                self._elements[i]
                                for i in self._depends_on_union(rel1.get_dimension(do_dimension["name"], p1))
                            },
                            {
                                self._elements[i] for i in rel2.get_dimension(other_dimension["name"], p2)
                            }
                        ) & OrderResult.EQUIVALENT == OrderResult.EQUIVALENT
                        for p1 in lp_do_dimension for p2 in lp_other_dimension
                ):
                    return True

        return False

    def _depends_on_union(self, elements_indices):
        """
        Returns the set of indices of elements in the dependsOn adjacency of the elements whose indices are in
        elements_indices
        :param elements_indices: a set of indices of elements
        :return: set of indices of elements in the dependsOn adjacency of the elements whose indices are in
        elements_indices
        """

        retval = set()

        for i in elements_indices:
            retval |= self._elements[i].get_depends_on_adjacency()

        return retval

