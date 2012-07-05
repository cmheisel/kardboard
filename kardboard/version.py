import os
import subprocess

version = "1.5"


def get_git_version():
    p = subprocess.Popen(['which git'], shell=True, stdout=subprocess.PIPE)
    returncode = os.wait()
    has_git = returncode[-1] if returncode else -1
    if has_git == 0:
        location = os.path.dirname(os.path.abspath(__file__))
        p = subprocess.Popen(
            ['cd %s && git describe --tags' % location],
            stdout=subprocess.PIPE, shell=True)
        result = p.communicate()[0]
        return '-%s' % result
    else:
        return ''

this_folder = os.path.dirname(os.path.abspath(__file__))

__git_version__ = get_git_version()
__version__ = version
VERSION = "%s%s" % (version, __git_version__)
