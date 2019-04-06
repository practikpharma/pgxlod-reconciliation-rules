#!/bin/bash

function printgreen() {
    printf "\\x1b[32m%s\\x1b[0m\\n" "$1"
}

function printred() {
    printf "\\x1b[31m%s\\x1b[0m\\n" "$1"
}

missing="false"

function checkDependency() {
    if [ "$(command -v "$1")" ]
    then
        printgreen "OK"
    else
        printred "MISSING"
        missing="true"
    fi
}

function checkTriple() {
    if [ "$(grep -c "$1" test/output.ttl)" -eq 1 ]
    then
        printgreen "OK"
    else
        printred "FAIL"
    fi
}

echo "Checking dependencies"
echo -n "python3... "
checkDependency "python3"

if [ ${missing} = "true" ]
then
    printred "=> Dependencies missing, check log";
else
    printgreen "=> Starting tests"
    python3 src/main.py --configuration test/test-conf.json --max-rows 10000 --integration-ontology test/pgxo+test.owl batch --output test/output.ttl

    echo -n "r1 owl:sameAs r2 "
    checkTriple "<http://pgxo.loria.fr/r1> <http://www.w3.org/2002/07/owl#sameAs> <http://pgxo.loria.fr/r2>"

    echo -n "r2 owl:sameAs r1 "
    checkTriple "<http://pgxo.loria.fr/r2> <http://www.w3.org/2002/07/owl#sameAs> <http://pgxo.loria.fr/r1>"

    echo -n "r3 owl:sameAs r1 "
    checkTriple "<http://pgxo.loria.fr/r3> <http://www.w3.org/2002/07/owl#sameAs> <http://pgxo.loria.fr/r1>"

    echo -n "r1 owl:sameAs r3 "
    checkTriple "<http://pgxo.loria.fr/r1> <http://www.w3.org/2002/07/owl#sameAs> <http://pgxo.loria.fr/r3>"

    echo -n "r3 owl:sameAs r2 "
    checkTriple "<http://pgxo.loria.fr/r3> <http://www.w3.org/2002/07/owl#sameAs> <http://pgxo.loria.fr/r2>"

    echo -n "r2 owl:sameAs r3 "
    checkTriple "<http://pgxo.loria.fr/r2> <http://www.w3.org/2002/07/owl#sameAs> <http://pgxo.loria.fr/r3>"

    echo -n "r5 skos:broadMatch r4 "
    checkTriple "<http://pgxo.loria.fr/r5> <http://www.w3.org/2004/02/skos/core#broadMatch> <http://pgxo.loria.fr/r4>"

    echo -n "r4 skos:narrowMatch r5 "
    checkTriple "<http://pgxo.loria.fr/r4> <http://www.w3.org/2004/02/skos/core#narrowMatch> <http://pgxo.loria.fr/r5>"

    echo -n "r7 skos:broadMatch r6 "
    checkTriple "<http://pgxo.loria.fr/r7> <http://www.w3.org/2004/02/skos/core#broadMatch> <http://pgxo.loria.fr/r6>"

    echo -n "r6 skos:narrowMatch r7 "
    checkTriple "<http://pgxo.loria.fr/r6> <http://www.w3.org/2004/02/skos/core#narrowMatch> <http://pgxo.loria.fr/r7>"

    echo -n "r7 owl:sameAs r12 "
    checkTriple "<http://pgxo.loria.fr/r7> <http://www.w3.org/2002/07/owl#sameAs> <http://pgxo.loria.fr/r12>"

    echo -n "r12 owl:sameAs r7 "
    checkTriple "<http://pgxo.loria.fr/r12> <http://www.w3.org/2002/07/owl#sameAs> <http://pgxo.loria.fr/r7>"

    echo -n "r12 skos:broadMatch r6 "
    checkTriple "<http://pgxo.loria.fr/r12> <http://www.w3.org/2004/02/skos/core#broadMatch> <http://pgxo.loria.fr/r6>"

    echo -n "r6 skos:narrowMatch r12 "
    checkTriple "<http://pgxo.loria.fr/r6> <http://www.w3.org/2004/02/skos/core#narrowMatch> <http://pgxo.loria.fr/r12>"

    echo -n "r15 skos:broadMatch r6 "
    checkTriple "<http://pgxo.loria.fr/r15> <http://www.w3.org/2004/02/skos/core#broadMatch> <http://pgxo.loria.fr/r6>"

    echo -n "r6 skos:narrowMatch r15 "
    checkTriple "<http://pgxo.loria.fr/r6> <http://www.w3.org/2004/02/skos/core#narrowMatch> <http://pgxo.loria.fr/r15>"

    echo -n "r12 skos:closeMatch r15 "
    checkTriple "<http://pgxo.loria.fr/r12> <http://www.w3.org/2004/02/skos/core#closeMatch> <http://pgxo.loria.fr/r15>"

    echo -n "r15 skos:closeMatch r12 "
    checkTriple "<http://pgxo.loria.fr/r15> <http://www.w3.org/2004/02/skos/core#closeMatch> <http://pgxo.loria.fr/r12>"

    echo -n "r7 skos:closeMatch r15 "
    checkTriple "<http://pgxo.loria.fr/r7> <http://www.w3.org/2004/02/skos/core#closeMatch> <http://pgxo.loria.fr/r15>"

    echo -n "r15 skos:closeMatch r7 "
    checkTriple "<http://pgxo.loria.fr/r15> <http://www.w3.org/2004/02/skos/core#closeMatch> <http://pgxo.loria.fr/r7>"

    echo -n "r8 skos:broadMatch r9 "
    checkTriple "<http://pgxo.loria.fr/r8> <http://www.w3.org/2004/02/skos/core#broadMatch> <http://pgxo.loria.fr/r9>"

    echo -n "r9 skos:narrowMatch r8 "
    checkTriple "<http://pgxo.loria.fr/r9> <http://www.w3.org/2004/02/skos/core#narrowMatch> <http://pgxo.loria.fr/r8>"

    echo -n "r10 skos:broadMatch r16 "
    checkTriple "<http://pgxo.loria.fr/r10> <http://www.w3.org/2004/02/skos/core#broadMatch> <http://pgxo.loria.fr/r16>"

    echo -n "r16 skos:narrowMatch r10 "
    checkTriple "<http://pgxo.loria.fr/r16> <http://www.w3.org/2004/02/skos/core#narrowMatch> <http://pgxo.loria.fr/r10>"

    echo -n "r11 skos:broadMatch r10 "
    checkTriple "<http://pgxo.loria.fr/r11> <http://www.w3.org/2004/02/skos/core#broadMatch> <http://pgxo.loria.fr/r10>"

    echo -n "r10 skos:narrowMatch r11 "
    checkTriple "<http://pgxo.loria.fr/r10> <http://www.w3.org/2004/02/skos/core#narrowMatch> <http://pgxo.loria.fr/r11>"

    echo -n "r11 skos:broadMatch r16 "
    checkTriple "<http://pgxo.loria.fr/r11> <http://www.w3.org/2004/02/skos/core#broadMatch> <http://pgxo.loria.fr/r16>"

    echo -n "r16 skos:narrowMatch r11 "
    checkTriple "<http://pgxo.loria.fr/r16> <http://www.w3.org/2004/02/skos/core#narrowMatch> <http://pgxo.loria.fr/r11>"

    echo -n "r13 skos:relatedMatch r14 "
    checkTriple "<http://pgxo.loria.fr/r13> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r14>"

    echo -n "r14 skos:relatedMatch r13 "
    checkTriple "<http://pgxo.loria.fr/r14> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r13>"

    echo -n "r13 skos:relatedMatch r8 "
    checkTriple "<http://pgxo.loria.fr/r13> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r8>"

    echo -n "r8 skos:relatedMatch r13 "
    checkTriple "<http://pgxo.loria.fr/r8> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r13>"

    echo -n "r13 skos:relatedMatch r9 "
    checkTriple "<http://pgxo.loria.fr/r13> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r9>"

    echo -n "r9 skos:relatedMatch r13 "
    checkTriple "<http://pgxo.loria.fr/r9> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r13>"

    echo -n "r13 skos:relatedMatch r15 "
    checkTriple "<http://pgxo.loria.fr/r13> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r15>"

    echo -n "r15 skos:relatedMatch r13 "
    checkTriple "<http://pgxo.loria.fr/r15> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r13>"

    echo -n "r13 skos:relatedMatch r12 "
    checkTriple "<http://pgxo.loria.fr/r13> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r12>"

    echo -n "r12 skos:relatedMatch r13 "
    checkTriple "<http://pgxo.loria.fr/r12> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r13>"

    echo -n "r13 skos:relatedMatch r7 "
    checkTriple "<http://pgxo.loria.fr/r13> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r7>"

    echo -n "r7 skos:relatedMatch r13 "
    checkTriple "<http://pgxo.loria.fr/r7> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r13>"

    echo -n "r13 skos:relatedMatch r6 "
    checkTriple "<http://pgxo.loria.fr/r13> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r6>"

    echo -n "r6 skos:relatedMatch r13 "
    checkTriple "<http://pgxo.loria.fr/r6> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r13>"

    echo -n "r13 skos:relatedMatch r5 "
    checkTriple "<http://pgxo.loria.fr/r13> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r5>"

    echo -n "r5 skos:relatedMatch r13 "
    checkTriple "<http://pgxo.loria.fr/r5> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r13>"

    echo -n "r13 skos:relatedMatch r4 "
    checkTriple "<http://pgxo.loria.fr/r13> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r4>"

    echo -n "r4 skos:relatedMatch r13 "
    checkTriple "<http://pgxo.loria.fr/r4> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r13>"

    echo -n "r13 skos:relatedMatch r3 "
    checkTriple "<http://pgxo.loria.fr/r13> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r3>"

    echo -n "r3 skos:relatedMatch r13 "
    checkTriple "<http://pgxo.loria.fr/r3> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r13>"

    echo -n "r13 skos:relatedMatch r2 "
    checkTriple "<http://pgxo.loria.fr/r13> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r2>"

    echo -n "r2 skos:relatedMatch r13 "
    checkTriple "<http://pgxo.loria.fr/r2> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r13>"

    echo -n "r13 skos:relatedMatch r1 "
    checkTriple "<http://pgxo.loria.fr/r13> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r1>"

    echo -n "r1 skos:relatedMatch r13 "
    checkTriple "<http://pgxo.loria.fr/r1> <http://www.w3.org/2004/02/skos/core#relatedMatch> <http://pgxo.loria.fr/r13>"

    triples_number=$(wc -l test/output.ttl | awk '{ $1 $2 ; print $1}')
    if [ "${triples_number}" = "52" ]
    then
        printgreen "52 triples generated"
    else
        printred "${triples_number} triples generated"
    fi

    rm test/output.ttl
fi
