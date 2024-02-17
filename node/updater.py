import subprocess
import threading
import typing
import time
import git
import logging
logger = logging.getLogger("updater")

from node.dir import BASEDIR

UPDATE_BRANCHES = ["main", "develop", "release"]

class Updater:
    def __init__(self):
        self.update_available = False
        self.repo = git.Repo(BASEDIR)

        # Get current branch
        self.current_branch = self.repo.active_branch.name
        logger.info(f"Current branch: {self.current_branch}")

    def run_cmd(self, command: typing.List[str]):
        return subprocess.check_output(command, encoding='utf8').strip()

    def check_for_updates(self):
        if self.current_branch not in UPDATE_BRANCHES:
            logger.warning(f"You are not on an update branch. Skipping update check.")
            return

        # Fetch latest changes from remote repository
        self.repo.remotes.origin.fetch()

        # Get latest commit hashes for local and remote branches
        local_branch = self.repo.active_branch

        # Get the corresponding remote tracking branch
        remote_branch = self.repo.remotes.origin.refs[local_branch.name]

        # Compare the local branch to the corresponding remote tracking branch
        comparison = local_branch.commit.diff(remote_branch.commit)

        # Compare commit hashes
        if comparison:
            logger.info("Updates available!")
            self.update_available = True
        else:
            logger.info("No updates available.")
            self.update_available = False
    
    def update(self):
        if self.update_available:
            try:
                self.repo.remotes.origin.pull()
                self.run_cmd(["./scripts/install.sh"])
            except Exception as e:
                logger.exception("Exception while updating")
        else:
            logger.warning("Cannot update, no updates available")

    def start(self):
        run_thread = threading.Thread(target=self.run, daemon=True)
        run_thread.start()
    
    def run(self):
        while True:
            self.check_for_updates()
            time.sleep(3600)    # Check every hour