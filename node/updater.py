import subprocess
import threading
import typing
import time
import logging
logger = logging.getLogger("updater")

from node.dir import BASEDIR

UPDATE_BRANCHES = ["main", "develop", "release"]

class Updater:
    def __init__(self):
        self.update_available = False

        # Get current branch
        self.current_branch = self.run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        logger.info(f"Current branch: {self.current_branch}")

    def run_cmd(self, command: typing.List[str]):
        return subprocess.run(command, capture_output=True, text=True, universal_newlines=True).stdout.strip()

    def check_for_updates(self):
        if self.current_branch not in UPDATE_BRANCHES:
            logger.warning(f"You are not on an update branch. Skipping update check.")
            return

        # Fetch latest changes from remote repository
        self.run_cmd(["git", "fetch"])

        # Get latest commit hashes for local and remote branches
        local_commit = self.run_cmd(["git", "rev-parse", "HEAD"])
        remote_commit = self.run_cmd(["git", "rev-parse", f"origin/{self.current_branch}"])

        # Compare commit hashes
        if local_commit != remote_commit:
            logger.info("Updates available!")
            self.update_available = True
        else:
            logger.info("No updates available.")
            self.update_available = False
    
    def update(self):
        if self.update_available:
            try:
                self.run_cmd(["git", "pull", "origin", self.current_branch])
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