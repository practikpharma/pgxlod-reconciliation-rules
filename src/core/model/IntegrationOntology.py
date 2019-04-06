import rdflib

__author__ = "Pierre Monnin"


class IntegrationOntology:
    """
    Integration ontology used to represent relationships and connect them with their components
    """

    def __init__(self, ontology_file_path, top_lp_properties):
        """
        Build the IntegrationOntology object
        :param ontology_file_path: file path for the integration ontology
        :param top_lp_properties: top linking predicates that will be used to link components with relationships. They
        should be subProperties of owl:topObjectProperty. For each linking predicate, its descendants and ancestors will
        be considered as well
        """

        self._ontology_graph = rdflib.Graph()
        self._ontology_graph.parse(ontology_file_path, format=rdflib.util.guess_format(ontology_file_path))
        self._linking_predicates = {}

        to_explore = set(top_lp_properties)
        while len(to_explore) != 0:
            p = to_explore.pop()

            # Querying ancestors
            res = self._ontology_graph.query("""
                SELECT distinct ?ancestor
                WHERE
                {
                    <%s> rdfs:subPropertyOf+ ?ancestor .
                }
            """ % p)

            ancestors = set()
            for row in res:
                ancestors.add(str(row["ancestor"]))

                if str(row["ancestor"]) not in self._linking_predicates and str(row["ancestor"]) not in to_explore:
                    to_explore.add(str(row["ancestor"]))

            # Querying descendants
            res = self._ontology_graph.query("""
                SELECT distinct ?descendant
                WHERE
                {
                    ?descendant rdfs:subPropertyOf+ <%s> .
                }
            """ % p)

            descendants = set()
            for row in res:
                descendants.add(str(row["descendant"]))

                if str(row["descendant"]) not in self._linking_predicates and str(row["descendant"]) not in to_explore:
                    to_explore.add(str(row["descendant"]))

            # Querying inverses
            res = self._ontology_graph.query("""
                SELECT DISTINCT ?inverse
                WHERE
                {
                    {
                        <%s> owl:inverseOf ?inverse .
                    }
                    UNION
                    {
                        ?inverse owl:inverseOf <%s> .
                    }
                }
            """ % (p, p))

            inverses = set()
            for row in res:
                inverses.add(str(row["inverse"]))

                if str(row["inverse"]) not in self._linking_predicates and str(row["inverse"]) not in to_explore:
                    to_explore.add(str(row["inverse"]))

            res = self._ontology_graph.query("""
                ASK
                {
                    <%s> rdf:type owl:SymmetricProperty .
                }
            """ % p)

            for row in res:
                if row:
                    inverses.add(p)

            self._linking_predicates[p] = {"ancestors": ancestors, "descendants": descendants, "inverses": inverses}

    def get_linking_predicates(self):
        """
        Returns the set of linking predicates of the integration ontology. Each linking predicate is used in at least
        on dimension
        :return: the set of linking predicates of the integration ontology
        """

        return set(self._linking_predicates.keys())

    def get_linking_predicate_ancestors(self, linking_predicate):
        """
        Returns the set of ancestors of the given linking predicate.
        :param linking_predicate: the linking predicate whose ancestors are needed
        :return: the set of ancestors of the given linking predicate
        """

        if linking_predicate not in self._linking_predicates:
            return set()

        return set(self._linking_predicates[linking_predicate]["ancestors"])

    def get_linking_predicate_inverses(self, linking_predicate):
        """
        Returns the set of inverses of the given linking predicate
        :param linking_predicate: the linking predicate whose inverses are needed
        :return: the set of inverses of the given linking predicate
        """

        if linking_predicate not in self._linking_predicates:
            return set()

        return set(self._linking_predicates[linking_predicate]["inverses"])

    def linking_predicates_descendants_expansion(self, linking_predicates):
        """
        Expands a set of linking predicates by adding their descendants
        :param linking_predicates: the initial seed set of linking predicates
        :return: a set containing the seed linking predicates and their descendants
        """

        retval = set(linking_predicates)

        for lp in linking_predicates:
            if lp in self._linking_predicates:
                retval |= self._linking_predicates[lp]["descendants"]

        return retval
