import os
import subprocess
import datetime

from django.utils.version import get_version


VERSION = (3, 1, 10, 'rc', 2)     # 'alpha', 'beta', 'rc', 'final'


def get_git_changeset():
    # Repository may not be found if __file__ is undefined, e.g. in a frozen
    # module.
    if "__file__" not in globals():
        return None
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    git_log = subprocess.run(
        'git log --pretty="format:%ct||%an||%s" --quiet -1 HEAD',
        capture_output=True,
        shell=True,
        cwd=repo_dir,
        text=True,
    )

    try:
        cmd_output = git_log.stdout.split('||')
        timestamp = cmd_output[0]
        tz = datetime.timezone.utc
        timestamp = datetime.datetime.fromtimestamp(int(timestamp), tz=tz)
    except Exception:
        return None

    return {'timestamp': timestamp.strftime("%Y/%m/%d %H:%M:%S"), 'author': cmd_output[1], 'content': cmd_output[2]}


__version__ = get_version(VERSION)
__version_git_change_set__ = get_git_changeset()
