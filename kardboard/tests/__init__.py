import os


def load_tests(loader, tests, pattern):
    """
        Constructs and returns a test suite for this module.
        See http://docs.python.org/dev/library/unittest.html#load-tests-protocol
        for more details.

        This is provided so that something like runtests.py will work in
        places like continuous.io -- since they don't support nose
        or other test discovery methods.
    """
    the_suite = loader.discover(os.path.dirname(os.path.abspath(__file__)))
    return the_suite


load_tests.__test__ = False  # Make nose ignore this
