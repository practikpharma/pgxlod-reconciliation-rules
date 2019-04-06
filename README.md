# pgxlod-reconciliation-rules

Python scripts applying reconciliation rules on a triplestore.

## Execution modes

### ``batch`` mode

Executes reconciliation rules on every relationship in the triplestore. 

#### Execution (without Docker)

```bash
python main.py --configuration conf.json --integration-ontology pgxo.owl --max-rows ResultSetsMaxRows --threads 4 batch --output output.ttl
```

where:

* *conf.json*: is the configuration file needed to configure the scripts -- see below
* *pgxo.owl*: is the ontology used to integrate and represent relationships
* *ResultSetMaxRows*: corresponds to the parameter ``ResultSetMaxRows`` of the virtuoso.ini file used to configure the virtuoso instance
* *threads*: number of threads
* *output.ttl*: is the path to the output TTL file where the generated links between relationships will be stored

#### Execution (in Docker)

You can use the target ``run`` of the provided Makefile that calls the Docker image with:

```bash
docker run --rm $(MAPUSER) -v ${PWD}/data:/data $(INAME):$(VERSION) --configuration /data/conf.json.example --integration-ontology data/pgxo.owl --max-rows 10000 --threads 4 batch --output /data/output.ttl
```

The ``data`` subdirectory of the current directory is shared with the Docker container as ``/data``. It is expected that
the JSON configuration file and the integration ontology file are in this directory. ``/data`` is also the directory where the output TTL file
will be stored. ``max-rows`` is set to 10000.

### ``explain`` mode

#### Execution (without Docker)

```bash
python main.py --configuration conf.json --integration-ontology pgxo.owl --max-rows ResultSetsMaxRows --threads 4 explain --uri1 URI1 --uri2 URI2
```

where:

* *conf.json*: is the configuration file needed to configure the scripts -- see below
* *pgxo.owl*: is the ontology used to integrate and represent relationships
* *ResultSetMaxRows*: corresponds to the parameter ``ResultSetMaxRows`` of the virtuoso.ini file used to configure the virtuoso instance
* *threads*: number of threads
* *URI1* and *URI2*: URIs of relationships to reconcile. The result will be explained for each dimension.

#### Execution (in Docker)

Not available.

## Input

### Configuration JSON file

A configuration JSON file is needed to configure the scripts. [An example is provided](data/conf.json.example).
It should contains:

```json
{
    "server-address": "http://127.0.0.1:8890/sparql",
    "url-json-conf-attribute": "format",
    "url-json-conf-value": "application/sparql-results+json",
    "url-default-graph-attribute": "default-graph-uri",
    "url-default-graph-value": "http://pgxlod.loria.fr/",
    "url-query-attribute": "query",
    "timeout": 10000000,
    "part-of-predicates": [
        "http://purl.obolibrary.org/obo/BFO_0000050"
    ],
    "has-part-predicates": [
        "http://purl.obolibrary.org/obo/BFO_0000051"
    ],
    "depends-on-predicates": [
        "http://purl.obolibrary.org/obo/RO_0002502"
    ],
    "integration-ontology-relationships-classes": [
        "http://pgxo.loria.fr/PharmacogenomicRelationship"
    ],
    "dimensions": [
        {
            "name": "GeneticFactor",
            "integration-ontology-top-classes": [
                "http://pgxo.loria.fr/GeneticFactor"
            ],
            "integration-ontology-top-linking-predicates": [
                "http://pgxo.loria.fr/isAssociatedWith",
                "http://pgxo.loria.fr/isNotAssociatedWith"
            ],
            "preorder": "PartOfPreorder",
            "comparison-ontology-base-uris": [
            ],
            "depends-on-similarity": false
        },
        {
            "name": "Drug",
            "integration-ontology-top-classes": [
                "http://pgxo.loria.fr/Drug"
            ],
            "integration-ontology-top-linking-predicates": [
                "http://pgxo.loria.fr/isAssociatedWith",
                "http://pgxo.loria.fr/isNotAssociatedWith"
            ],
            "preorder": "MsciPreorder",
            "comparison-ontology-base-uris": [
                "http://purl.obolibrary.org/obo/CHEBI_",
                "http://bio2rdf.org/chebi:",
                "http://identifiers.org/chebi/",
                "http://purl.bioontology.org/ontology/UATC/",
                "http://bio2rdf.org/atc:",
                "http://identifiers.org/atc/"
            ],
            "depends-on-similarity": false
        },
        {
            "name": "Phenotype",
            "integration-ontology-top-classes": [
                "http://pgxo.loria.fr/Phenotype"
            ],
            "integration-ontology-top-linking-predicates": [
                "http://pgxo.loria.fr/isAssociatedWith",
                "http://pgxo.loria.fr/isNotAssociatedWith"
            ],
            "preorder": "MsciPreorder",
            "comparison-ontology-base-uris": [
                "http://purl.bioontology.org/ontology/MESH/",
                "http://bio2rdf.org/mesh:",
                "http://identifiers.org/mesh/"
            ],
            "depends-on-similarity": true
        }
    ],
    "output-equal-predicate": "http://www.w3.org/2002/07/owl#sameAs",
    "output-equiv-predicate": "http://www.w3.org/2004/02/skos/core#closeMatch",
    "output-leq-predicate": "http://www.w3.org/2004/02/skos/core#broadMatch",
    "output-geq-predicate": "http://www.w3.org/2004/02/skos/core#narrowMatch",
    "output-do-related-predicate": "http://www.w3.org/2004/02/skos/core#relatedMatch"
}
```

with:

* _server-address_: address of the SPARQL endpoint to query
* _url-json-conf-attribute_: URL attribute to use to get JSON results
* _url-json-conf-value_: value of the _url-json-conf-attribute_ to get JSON results
* _url-default-graph-attribute_: URL attribute to use to define the default graph
* _url-default-graph-value_: value of _url-default-graph-attribute_ to define the default graph
* _url-query-attribute_: URL attribute to use to define the query
* _timeout_: timeout value for HTTP requests
* _part-of-predicates_: URIs of predicates corresponding to a partOf relationship
* _has-part-predicates_: URIs of predicates corresponding to the inverse of a partOf relationship
* _depends-on-predicates_: URIs of predicates corresponding to a dependsOn relationship
* _integration-ontology-relationships-classes_: URIs of classes from the integration ontology that are used to identify 
relationships
* _dimensions_: array of dimensions. Each dimension should contain:
  * _name_: name identifying the dimension
  * _integration-ontology-top-classes_: classes of the integration ontology that are instantiated by elements of this 
  dimension. Subclasses will be considered as well.
  * _integration-ontology-top-linking-predicates_: predicates of the integration ontology that are used to connect 
  elements of this dimension with relationships. Subproperties will be considered as well
  * _preorder_: preorder to use for comparisons on this dimension. Value should be ``PartOfPreorder`` or ``MsciPreorder``.
  * _comparison-ontology-base-uris_: base URIs of the ontologies to use for the ``MsciPreorder``
  * _depends-on-similarity_: boolean enabling dependsOn similarity comparison on this dimension
* _output-equal-predicate_: URI of a predicate to use to identify equal relationships
* _output-equiv-predicate_: URI of a predicate to use to identify equivalent relationships
* _output-leq-predicate_: URI of a predicate to use to identify lower or equal relationships
* _output-geq-predicate_: URI of a predicate to use to identify greater or equal relationships
* _output-do-related-predicate_: URI of a predicate to use to identify relationships that are related through dependsOn

## Tests

A ``test/pgxo+test.owl`` file is available to test the scripts. It should be imported in a triplestore instance
that will then be queried. After the import, start the tests with ``make test``. The description of the test cases 
and their results can be found in [test/documentation-tests.pdf](test/documentation-tests.pdf)

## Dependencies

* Python3.6
* ``requests`` Python module 
* ``rdflib`` Python module 
* ``tqdm`` Python module 

## References

* \[1\] Monnin, P., Jonquet, C., Legrand, J., Napoli, A., & Coulet, A. (2017).
PGxO: A very lite ontology to reconcile pharmacogenomic knowledge units.
In PeerJ Preprints 5:e3140v1 https://doi.org/10.7287/peerj.preprints.3140v1
* \[2\] Monnin, P., Legrand, J., Husson, G., Ringot, P., Tchechmedjiev, A., Jonquet, C., 
Napoli, A., & Coulet, A. (2018). 
PGxO and PGxLOD: a reconciliation of pharmacogenomic knowledge of various provenances, 
enabling further comparison. bioRxiv, 390971.
