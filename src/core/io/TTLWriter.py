__author__ = "Pierre Monnin"


class TTLWriter:
    def __init__(self, file_path):
        self._file = open(file_path, 'w')

    def write_triple(self, subject, predicate, obj):
        self._file.write(subject + " " + predicate + " " + obj + ".\n")

    def close(self):
        self._file.close()
