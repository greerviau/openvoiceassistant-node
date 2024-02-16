import subprocess
import threading
import time
import logging
logger = logging.getLogger("updater")

class Updater:
    def __init__(self):
        self.update_available = False
        self.update_branch_name = "release"

    def check_for_updates(self):
        # Get current branch
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
        current_branch = result.stdout.strip()
        
        if current_branch != self.update_branch_name:
            logger.warning(f"You are not on the {self.update_branch_name} branch. Skipping update check.")
            return

        # Fetch latest changes from remote repository
        subprocess.run(["git", "fetch"])

        # Get latest commit hashes for local and remote branches
        local_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip()
        remote_commit = subprocess.check_output(["git", "rev-parse", f"origin/{current_branch}"]).strip()

        # Compare commit hashes
        if local_commit != remote_commit:
            logger.info("Updates available!")
            self.update_available = True
        else:
            logger.info("No updates available.")
    
    def update(self):
        if self.update_available:
            try:
                subprocess.run(["git", "pull"])
                subprocess.run(["./scripts/install.sh"])
                subprocess.run(["systemctl", "restart", "ova_node.service"])
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