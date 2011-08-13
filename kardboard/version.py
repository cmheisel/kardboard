import os

from kardboard.util import get_git_version

this_folder = os.path.dirname(os.path.abspath(__file__))
version = file(os.path.join(this_folder, 'VERSION.txt'), 'r').read()

__git_version__ = get_git_version()
__version__ = version
VERSION = "%s%s" % (version, __git_version__)