# -*- coding: utf-8 -*-
# Author: Douglas Creager <dcreager@dcreager.net>
# This file is placed into the public domain.

from __future__ import print_function

import json
import os.path
from subprocess import Popen, PIPE
import urllib

from prism.memorize import memorize

__all__ = ["get_git_version"]

RELEASE_VERSION_FILE = os.path.join(os.path.dirname(__file__), 'VERSION')
GIT_REPO = os.path.join(os.path.dirname(__file__), '..', '.git')

REPO_LOCATION = 'Stumblinbear/Prism'

def get_git_version(abbrev=4, cwd=None):
    try:
        p = Popen(['git', '--git-dir=%s' % GIT_REPO,
                   'fetch', '--tags'])
        p = Popen(['git', '--git-dir=%s' % GIT_REPO,
                   'describe', '--abbrev=%d' % abbrev, '--tags'],
                  stdout=PIPE, stderr=PIPE)
        stdout, _stderr = p.communicate()
        return stdout.strip().decode('utf-8', 'ignore')
    except Exception:
        return None

def read_release_version():
    try:
        with open(RELEASE_VERSION_FILE) as f:
            return f.readline().strip()
    except Exception:
        return None

def write_release_version(version):
    with open(RELEASE_VERSION_FILE, 'w') as f:
        f.write("%s\n" % version)

def get_version(abbrev=4):
    # determine the version from git and from RELEASE-VERSION
    git_version = get_git_version(abbrev)
    release_version = read_release_version()

    # if we have a git version, it is authoritative
    if git_version:
        if git_version.count('-') > 2:
            git_version = '-'.join(git_version.split('-')[:-2])
        if git_version != release_version:
            write_release_version(git_version)
        return git_version
    elif release_version:
        return release_version
    else:
        raise ValueError('Cannot find a version number!')

def github_api_call_(extention):
    return json.loads(urllib.request.urlopen('https://api.github.com/' + extention).read().decode('utf-8'))

def github_api_call(api, page=0):
    return github_api_call_('repos/%s/%s?page=%s' % (REPO_LOCATION, api, page))

@memorize(60 * 60 * 60 * 24)
def get_new_versions(version):
    if version is None:
        return False, None, None, None

    try:
        if github_api_call_('rate_limit')['rate']['remaining'] < 3:
            return True, None, None, None

        tags = github_api_call('tags')
        releases = github_api_call('releases')
        recent_releases = []

        for i in range(0, 2 if len(tags) > 2 else len(tags)):
            release_info = None
            for release in releases:
                if release['tag_name'] == tags[i]['name']:
                    release_info = release
                    break

            if release_info is None:
                continue

            release_name, release_hash, release_date = tags[i]['name'], tags[i]['commit']['sha'], release_info['published_at']
            recent_releases.append({
                        'name': release_name,
                        'hash': release_hash,
                        'date': release_date,
                        'changes': get_version_changes(release_hash, None if i == len(tags) - 1 else tags[i + 1]['commit']['sha'])
                    })
        dev_changes = get_dev_changes(recent_releases[0]['hash'])
        return False, dev_changes, recent_releases, len(tags)
    except Exception as e:
        return False, None, None, None

def get_dev_changes(end_hash):
    try:
        page = 0
        changes = []

        while True:
            all_commits = github_api_call('commits', page)

            for commit in all_commits:
                if commit['sha'] == end_hash:
                    return changes
                changes.append((commit['sha'][:6], commit['commit']['message'], commit['html_url'], commit['commit']['author']['date']))

            if len(all_commits) != 0:
                break

            page += 1

        return changes
    except Exception as e:
        return None

def get_version_changes(start_hash, end_hash):
    try:
        page = 0
        changes = None

        while True:
            all_commits = github_api_call('commits', page)

            for commit in all_commits:
                if changes is None:
                    if commit['sha'] == start_hash:
                        changes = [(commit['sha'][:6], commit['commit']['message'], commit['html_url'], commit['commit']['author']['date'])]
                else:
                    if commit['sha'] == end_hash:
                        return changes

                    changes.append((commit['sha'][:6], commit['commit']['message'], commit['html_url'], commit['commit']['author']['date']))

            if len(all_commits) != 0:
                break

            page += 1

        return changes
    except:
        return None

if __name__ == "__main__":
    print(get_version())
