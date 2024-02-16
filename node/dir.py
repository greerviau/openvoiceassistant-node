import os

BASEDIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../"))
LOGSDIR = os.path.join(BASEDIR, 'logs')
SOUNDSDIR = os.path.join(BASEDIR, 'sounds')
FILESDIR = os.path.join(BASEDIR, 'files')
WAKEWORDMODELSDIR = os.path.join(BASEDIR, "wakeword_models")