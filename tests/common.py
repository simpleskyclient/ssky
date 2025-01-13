import os
from time import sleep
from dotenv import load_dotenv

from ssky.ssky_session import SskySession

def setup(envs_to_delete=[], no_session_file=False, interval=0):
    if interval > 0:
        sleep(interval)
    load_dotenv('tests/.env')
    for name in envs_to_delete:
        del os.environ[name]
    if no_session_file:
        if os.path.exists(os.path.expanduser('~/.ssky')):
            os.remove(os.path.expanduser('~/.ssky'))

def teardown():
    pass