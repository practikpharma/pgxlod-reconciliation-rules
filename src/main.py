import argparse
import json
import logging

from core.io.CacheManager import CacheManager
from core.io.ServerManager import ServerManager
from core.io.TTLWriter import TTLWriter
from core.io.TqdmLoggingHandler import TqdmLoggingHandler
from core.model.DimensionOntology import DimensionOntology
from core.model.IntegrationOntology import IntegrationOntology
from core.model.RDFGraph import RDFGraph
from core.reconciliation.preorders import OrderResult
from core.reconciliation.relationships import RelationshipsModel

__author__ = "Pierre Monnin"


def load_configuration(configuration_file_path):
    with open(configuration_file_path, 'r') as configuration_file:
        configuration_parameters = json.load(configuration_file, encoding="utf-8")

    expected_fields = [
        "server-address",
        "url-json-conf-attribute",
        "url-json-conf-value",
        "url-default-graph-attribute",
        "url-default-graph-value",
        "url-query-attribute",
        "timeout",
        "part-of-predicates",
        "has-part-predicates",
        "depends-on-predicates",
        "integration-ontology-relationships-classes",
        "dimensions",
        "output-equal-predicate",
        "output-equiv-predicate",
        "output-leq-predicate",
        "output-geq-predicate",
        "output-do-related-predicate"
    ]

    expected_dimension_fields = [
        "name",
        "integration-ontology-top-classes",
        "integration-ontology-top-linking-predicates",
        "preorder",
        "comparison-ontology-base-uris",
        "depends-on-similarity"
    ]

    configuration_errors = []
    for field in expected_fields:
        if field not in configuration_parameters:
            configuration_errors.append("Missing field: " + field)

        elif field == "dimensions":
            for i, d in enumerate(configuration_parameters[field]):
                for dimension_field in expected_dimension_fields:
                    if dimension_field not in d:
                        configuration_errors.append("Missing field: dimension " + str(i + 1) + " / " + dimension_field)

                    elif dimension_field == "preorder":
                        if d[dimension_field] not in {"PartOfPreorder", "MsciPreorder"}:
                            configuration_errors.append("Invalid preorder in dimension " + str(i + 1))

    if len(configuration_errors) != 0:
        raise KeyError("Errors in JSON configuration file: " + str(configuration_errors))

    return configuration_parameters


def main():
    # Parsing command line parameters and necessary configuration
    parser = argparse.ArgumentParser()
    parser.add_argument("--configuration", help="JSON file containing the configuration for the program "
                        "(triplestore address, dimensions, ...)", required=True, dest="configuration_file_path")
    parser.add_argument("--max-rows", dest="max_rows", help="Value of the parameter ResultSetMaxRows in virtuoso.ini",
                        required=True, type=int, default=10000)
    parser.add_argument("--integration-ontology", dest="integration_ontology_file_path",
                        help="File path for the OWL file of the integration ontology", required=True)
    parser.add_argument("--threads", dest="nb_threads", help="Number of threads", type=int, default=1)
    subparsers = parser.add_subparsers(title="Subcommands", description="Valid subcommands", dest="subcommand",
                                       help="Subcommands changing the execution mode")

    # Subcommand batch
    batch_parser = subparsers.add_parser("batch", help="Run PGxLOD-Reconciliation-Rules in batch mode on the entire "
                                                       "Knowledge Base")
    batch_parser.add_argument("--output", help="Path to the output TTL file", required=True)

    # Subcommand explain
    explain_parser = subparsers.add_parser("explain", help="Run PGxLOD-Reconciliation-Rules in a mode explaining the "
                                                           "result for a pair of URIs of relationships")
    explain_parser.add_argument("--uri1", dest="uri1", help="URI of the first relationship to compare",
                                required=True, type=str)
    explain_parser.add_argument("--uri2", dest="uri2", help="URI of the second relationship to compare",
                                required=True, type=str)
    args = parser.parse_args()

    # Logging parameters
    logger = logging.getLogger()
    tqdm_logging_handler = TqdmLoggingHandler()
    tqdm_logging_handler.setFormatter(logging.Formatter(fmt="[%(asctime)s][%(levelname)s] %(message)s"))
    logger.addHandler(tqdm_logging_handler)
    logger.setLevel(logging.INFO)

    logger.info("PGxLOD-Reconciliation rules")
    configuration_parameters = {}

    try:
        # Loading configuration
        configuration_parameters = load_configuration(args.configuration_file_path)

    except KeyError as e:
        logger.critical(str(e))
        exit(-1)

    # Global Cache Manager
    cache_manager = CacheManager()

    # Loading IntegrationOntology
    logger.info("Building Integration Ontology Model")
    integration_ontology = IntegrationOntology(
        args.integration_ontology_file_path,
        {predicate_uri
         for d in configuration_parameters["dimensions"]
         for predicate_uri in d["integration-ontology-top-linking-predicates"]}
    )

    # RDF graph (owl:sameAs, rdfs:subClassOf, rdf:type, dependsOn, partOf and linking predicates adjacencies)
    rdf_graph = RDFGraph(
        cache_manager,
        ServerManager(configuration_parameters, args.max_rows),
        integration_ontology,
        configuration_parameters["part-of-predicates"],
        configuration_parameters["has-part-predicates"],
        configuration_parameters["depends-on-predicates"]
    )

    # Loading dimension ontologies
    dimension_ontologies = {}
    for i, d in enumerate(configuration_parameters["dimensions"]):
        logger.info("Building %s dimension ontology" % d["name"])
        logger.info("Base URIs: " + str(d["comparison-ontology-base-uris"]))

        dimension_ontologies[d["name"]] = DimensionOntology(
            d["comparison-ontology-base-uris"],
            configuration_parameters,
            args.max_rows,
            args.nb_threads,
            cache_manager,
            rdf_graph
        )

    # Building relationships model
    logging.info("Building relationships model")
    relationships = RelationshipsModel(
        rdf_graph,
        integration_ontology,
        dimension_ontologies,
        configuration_parameters,
        cache_manager
    )

    if args.subcommand == "batch":
        logger.info("Batch mode")
        logger.info("Reconciling relationships")

        ttl_writer = TTLWriter(args.output)

        for result in relationships.reconcile():
            if result["order_result"] == OrderResult.EQUAL:
                ttl_writer.write_triple("<" + cache_manager.get_element_from_index(result["uri_index_1"]) + ">",
                                        "<" + configuration_parameters["output-equal-predicate"] + ">",
                                        "<" + cache_manager.get_element_from_index(result["uri_index_2"]) + ">")
                ttl_writer.write_triple("<" + cache_manager.get_element_from_index(result["uri_index_2"]) + ">",
                                        "<" + configuration_parameters["output-equal-predicate"] + ">",
                                        "<" + cache_manager.get_element_from_index(result["uri_index_1"]) + ">")

            elif result["order_result"] == OrderResult.EQUIVALENT:
                ttl_writer.write_triple("<" + cache_manager.get_element_from_index(result["uri_index_1"]) + ">",
                                        "<" + configuration_parameters["output-equiv-predicate"] + ">",
                                        "<" + cache_manager.get_element_from_index(result["uri_index_2"]) + ">")
                ttl_writer.write_triple("<" + cache_manager.get_element_from_index(result["uri_index_2"]) + ">",
                                        "<" + configuration_parameters["output-equiv-predicate"] + ">",
                                        "<" + cache_manager.get_element_from_index(result["uri_index_1"]) + ">")

            elif result["order_result"] == OrderResult.LEQ:
                ttl_writer.write_triple("<" + cache_manager.get_element_from_index(result["uri_index_1"]) + ">",
                                        "<" + configuration_parameters["output-leq-predicate"] + ">",
                                        "<" + cache_manager.get_element_from_index(result["uri_index_2"]) + ">")
                ttl_writer.write_triple("<" + cache_manager.get_element_from_index(result["uri_index_2"]) + ">",
                                        "<" + configuration_parameters["output-geq-predicate"] + ">",
                                        "<" + cache_manager.get_element_from_index(result["uri_index_1"]) + ">")

            elif result["order_result"] == OrderResult.GEQ:
                ttl_writer.write_triple("<" + cache_manager.get_element_from_index(result["uri_index_1"]) + ">",
                                        "<" + configuration_parameters["output-geq-predicate"] + ">",
                                        "<" + cache_manager.get_element_from_index(result["uri_index_2"]) + ">")
                ttl_writer.write_triple("<" + cache_manager.get_element_from_index(result["uri_index_2"]) + ">",
                                        "<" + configuration_parameters["output-leq-predicate"] + ">",
                                        "<" + cache_manager.get_element_from_index(result["uri_index_1"]) + ">")

            elif result["order_result"] == OrderResult.DO_RELATED:
                ttl_writer.write_triple("<" + cache_manager.get_element_from_index(result["uri_index_1"]) + ">",
                                        "<" + configuration_parameters["output-do-related-predicate"] + ">",
                                        "<" + cache_manager.get_element_from_index(result["uri_index_2"]) + ">")
                ttl_writer.write_triple("<" + cache_manager.get_element_from_index(result["uri_index_2"]) + ">",
                                        "<" + configuration_parameters["output-do-related-predicate"] + ">",
                                        "<" + cache_manager.get_element_from_index(result["uri_index_1"]) + ">")

        ttl_writer.close()

    elif args.subcommand == "explain":
        logger.info("Explain mode")
        if cache_manager.is_element_in_cache(args.uri1) and cache_manager.is_element_in_cache(args.uri2):
            relationships.explain_reconciliation(
                cache_manager.get_element_index(args.uri1),
                cache_manager.get_element_index(args.uri2)
            )

        else:
            logger.critical("Incorrect URIs")
            logger.critical("URI 1 in cache: " + str(cache_manager.is_element_in_cache(args.uri1)))
            logger.critical("URI 2 in cache: " + str(cache_manager.is_element_in_cache(args.uri2)))


if __name__ == '__main__':
    main()
