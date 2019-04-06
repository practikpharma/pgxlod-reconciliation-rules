import abc
import enum

__author__ = "Pierre Monnin"


class OrderResult(enum.Flag):
    """
    Represents the ordering result between two elements
    """

    EQUAL = 0b01111
    EQUIVALENT = 0b01110
    LEQ = 0b00100
    GEQ = 0b01000
    INCOMPARABLE = 0b0000
    DO_RELATED = 0b10000  # DO = dependsOn (specific complex similarity)


class Preorder:
    """
    Represents an abstract preorder
    """

    @abc.abstractmethod
    def _leq(self, set1, set2):
        """
        Returns true if set1 <= set2 according to preorder
        :param set1: set1 to compare, contains RelationshipElements
        :param set2: set2 to compare, contains RelationshipElements
        :return: true if set1 <= set2
        """

        pass

    def compare(self, set1, set2):
        """
        Compare two sets of RelationshipElements w.r.t the preorder
        :param set1: First set of RelationshipElements (should be instances, not indices)
        :param set2: Second set of RelationshipElements (should be instances, not indices)
        :return: OrderResult.EQUAL, EQUIVALENT, LEQ, GEQ or INCOMPARABLE
        """

        if set1 == set2:
            return OrderResult.EQUAL

        if self._leq(set1, set2):
            if self._leq(set2, set1):
                return OrderResult.EQUIVALENT

            return OrderResult.LEQ

        if self._leq(set2, set1):
            return OrderResult.GEQ

        return OrderResult.INCOMPARABLE


class PartOfPreorder(Preorder):
    """
    Preorder using the set inclusion and partOf relation to compare sets of RelationshipElements
    """

    def _leq(self, set1, set2):
        if len(set2) == 0:
            return True

        if len(set1) != 0:
            return all(i1 in set2 or any(i1.is_part_of(i2) for i2 in set2) for i1 in set1)

        return False


class MsciPreorder(Preorder):
    """
    Preorder using the set inclusion and the most specific classes instantiated (MSCI) subsumption to compare sets of
    RelationshipElements
    """

    def __init__(self, dimension_ontology):
        """
        Builds the MsciPreorder
        :param dimension_ontology: the DimensionOntology to use for the MSCI operation
        """

        self._dimension_ontology = dimension_ontology

    def _leq(self, set1, set2):
        if len(set2) == 0:
            return True

        if len(set1) != 0:
            return all(
                i1 in set2
                or
                (
                    len(i1.msci(self._dimension_ontology)) != 0
                    and
                    all(
                        any(
                            any(
                                self._dimension_ontology.is_subsumed(c1, c2)
                                for c2 in i2.msci(self._dimension_ontology)
                            ) for i2 in set2)
                        for c1 in i1.msci(self._dimension_ontology)
                    )
                )
                for i1 in set1
            )

        return False
