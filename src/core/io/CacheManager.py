__author__ = "Pierre Monnin"


class CacheManager:
    def __init__(self):
        self._cache = {}
        self._inverse_cache = []

    def get_element_index(self, element):
        if element not in self._cache:
            self._cache[element] = len(self._cache)
            self._inverse_cache.append(element)

        return self._cache[element]

    def get_element_from_index(self, index):
        if index > len(self._inverse_cache):
            return ""

        return self._inverse_cache[index]

    def is_element_in_cache(self, element):
        return element in self._cache

    def get_size(self):
        return len(self._cache)

    def get_element_indexes_from_start_string(self, start_string):
        ret_val = set()

        for e in self._cache:
            if e.startswith(start_string):
                ret_val.add(self._cache[e])

        return ret_val

    def __str__(self):
        retval = "-- CacheManager --\n"
        for uri, i in self._cache.items():
            retval += uri + " <=> " + str(i) + "\n"
        retval += "--"
        return retval
