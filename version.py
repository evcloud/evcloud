import os
import subprocess
import datetime

from django.utils.version import get_complete_version

VERSION = (4, 9, 0, 'final', 0)     # 'alpha', 'beta', 'rc', 'final'


def get_git_changeset():
    # Repository may not be found if __file__ is undefined, e.g. in a frozen
    # module.
    if "__file__" not in globals():
        return None
    repo_dir = os.path.dirname(os.path.abspath(__file__))

    git_log = subprocess.run(
        "git for-each-ref --count=3 --sort='-taggerdate' "
        "--format='%(refname:short) || %(taggerdate:format:%s) || %(*authorname) || %(*authoremail) || %(subject)'"
        " refs/tags/*",
        capture_output=True,
        shell=True,
        cwd=repo_dir,
        text=True,
    )

    try:
        cmd_output = git_log.stdout
        lines = cmd_output.split('\n')[0:3]
        tz = datetime.timezone.utc
        tags = []
        for line in lines:
            tag = line.split('||')
            if len(tag) == 5:
                tag[1] = datetime.datetime.fromtimestamp(int(tag[1]), tz=tz)
                tag[4] = tag[4].replace('*', '\n*')
                tags.append(tag)


    except Exception:
        return None
    return tags

def get_main_version(version=None):
    """Return main version (X.Y[.Z]) from VERSION."""
    version = get_complete_version(version)
    version_ = ".".join(str(x) for x in version[:3])
    return f'v{version_}'

__version__ = get_main_version(VERSION)
__version_git_change_set__ = get_git_changeset()
