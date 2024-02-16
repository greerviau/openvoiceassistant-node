import os
from datetime import datetime

BASEDIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))
SOUNDSDIR = os.path.join(BASEDIR, 'sounds')
FILESDIR = os.path.join(BASEDIR, 'files')
WAKEWORDMODELSDIR = os.path.join(BASEDIR, "wakeword_models")

now = datetime.now()
LOGSDIR = os.path.join(BASEDIR, 'logs', now.strftime("%m-%Y/%d"))
file = now.strftime("log_%H-%M-%S.log")
LOGFILE = os.path.join(LOGSDIR, file)

os.makedirs(FILESDIR, exist_ok=True)
os.makedirs(LOGSDIR, exist_ok=True)
