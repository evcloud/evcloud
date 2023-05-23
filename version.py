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

    # %(*refname) %(*authorname) %(*authoremail) %(*authordate) %(*subject)
    get_tag = subprocess.run(
        'git log --pretty=format:"%an || %ae || %at || %s || %d" -100',
        capture_output=True,
        shell=True,
        cwd=repo_dir,
        text=True,
    )
    try:
        cmd_output = get_tag.stdout
        lines = cmd_output.split('\n')
        # {tag: [[作者， 时间， 提交内容]]}
        tz = datetime.timezone.utc
        git_tag_dict = {}
        git_tag_info = []
        tag_count = 1
        tag = None
        for line in lines:
            if tag_count == 4:
                break

            commit_info = line.split('||')
            if commit_info[4].startswith('  (HEAD -> develop, tag:') or commit_info[4].startswith('  (HEAD -> master, tag:'):
                com_tag = commit_info[4].split(',')[1]
                commit_info[4] = '  (' + com_tag.replace(' ', '', 1) + ')'

            if commit_info[4].startswith('  (tag:'):
                if tag:
                    git_tag_dict[tag] = git_tag_info
                    tag_count += 1
                tag = commit_info[4].replace('  (tag: ', '').replace(')', '')
                git_tag_info = []
            commit_info[2] = datetime.datetime.fromtimestamp(int(commit_info[2]), tz=tz)
            commit_info[4] = commit_info[4].replace(' ', '')
            git_tag_info.append(commit_info)

    except Exception:
        return None

    return git_tag_dict


__version__ = get_version(VERSION)
__version_git_change_set__ = get_git_changeset()
