import argparse
import logging
import os
import subprocess
import json
import giturlparse

PROG_NAME = "git-repo-sync"
REPO_LIST_DIR = "repo-list"
REPO_LIST_FILE = "list.json"
SYNCED_DIR = "synced-repos"
log = logging.getLogger(PROG_NAME)


def is_dir_rw(dir_string):
    return os.path.isdir(dir_string) and os.access(dir_string, os.W_OK) and os.access(dir_string, os.R_OK)


def parse_dir(dir_string):
    if is_dir_rw(dir_string):
        return dir_string
    raise argparse.ArgumentTypeError("%r is not a directory with rw permissions." % dir_string)


def is_git_url(url_string):
    try:
        giturlparse.parse(url_string)
    except giturlparse.parser.ParserError:
        raise argparse.ArgumentTypeError("%r is not a valid git url." % url_string)
    return url_string


# clone or pull repo
def git_update(url, path):
    if is_dir_rw(path):
        log.debug("Pulling %s into %s", url, path)
        pull = subprocess.run(["git", "pull"], cwd=path)
        # throw error if git pull fail
        pull.check_returncode()
    else:
        log.debug("Cloning %s into %s", url, path)
        clone = subprocess.run(["git", "clone", url, path])
        clone.check_returncode()


def main():
    parser = argparse.ArgumentParser(prog=PROG_NAME)
    parser.add_argument("sync_dir", type=parse_dir, help="directory to store synced data in")
    parser.add_argument("repo_list", type=is_git_url, help="url of the repo that stores the repo list")
    parser.add_argument("-l", "-log", dest="log_level", default="DEBUG",
                        choices=['CRITICAL', 'FATAL', 'ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'NOTSET'],
                        help="log level")
    args = parser.parse_args()

    log.setLevel(args.log_level)

    log.debug("Parsed Args %s", str(vars(args)))

    # clone repo directory repo
    repo_list_path = os.path.join(args.sync_dir, REPO_LIST_DIR)
    git_update(args.repo_list, repo_list_path)

    repo_list_file_path = os.path.join(repo_list_path, REPO_LIST_FILE)
    log.debug("Starting reading %s", repo_list_file_path)
    with open(repo_list_file_path) as repo_list_file:
        repo_list_text = repo_list_file.read()
    repo_list = json.loads(repo_list_text)

    if not isinstance(repo_list, list):
        log.fatal("%s is not a list", repo_list_text)

    log.debug("Updating all repos")
    for repo in repo_list:
        if "dir" in repo and "url" in repo and is_git_url(repo["url"]):
            repo_path = os.path.join(args.sync_dir, SYNCED_DIR, repo["dir"])
            git_update(repo["url"], repo_path)
        else:
            log.fatal("%s is not a valid repo entry", str(repo))



main()
