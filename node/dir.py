import os

BASEDIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))
SOUNDSDIR = os.path.join(BASEDIR, "sounds")
FILESDIR = os.path.join(BASEDIR, "files")
WAKEWORDMODELSDIR = os.path.join(BASEDIR, "wakeword_models")

LOGSDIR = os.path.join(BASEDIR, "logs")
LOGFILE = os.path.join(LOGSDIR, "node.log")

os.makedirs(FILESDIR, exist_ok=True)
os.makedirs(LOGSDIR, exist_ok=True)