import json
import os
import sys
import atproto
import atproto_client

class SskySession:

    class Session:
        def __init__(self, client=None, profile=None):
            self.client = client
            self.profile = profile

    config_path = os.path.expanduser('~/.ssky')
    session = None

    login_failed = Session()

    class Status:
        NOT_LOGGED_IN = 0,
        LOGGED_IN = 1,
        LOGIN_FAILED = 2

    @classmethod
    def at_login_internal(cls, handle=None, password=None, session_string=None) -> Session:
        client = atproto.Client()
        profile = client.login(login=handle, password=password, session_string=session_string)
        return cls.Session(client, profile)

    @classmethod
    def login_internal(cls, handle=None, password=None) -> None:
        if SskySession.session is None:
            var_user = os.environ.get('SSKY_USER')
            if var_user is not None:
                handle, password = var_user.split(':')
                cls.session = cls.at_login_internal(handle=handle, password=password)
            elif handle is not None and password is not None:
                cls.session = cls.at_login_internal(handle=handle, password=password)
            elif os.path.exists(cls.config_path) and os.path.isfile(cls.config_path):
                with open(cls.config_path, 'r') as f:
                    persistent_config = json.load(f)
                    session_string = persistent_config.get('session_string')
                    cls.session = cls.at_login_internal(session_string=session_string)
            else:
                cls.session = cls.login_failed
                raise atproto_client.exceptions.LoginRequiredError('No credentials found. Please set SSKY_USER or run ssky login')

    @classmethod
    def persist_internal(cls) -> None:
        if cls.session is not None and cls.session is not cls.login_failed:
            session_string = cls.session.client.export_session_string()
            with open(cls.config_path, 'w') as f:
                json.dump({
                    'session_string': session_string
                }, f)

    @classmethod
    def status(cls) -> int:
        if cls.session is None:
            return cls.Status.NOT_LOGGED_IN
        elif cls.session is cls.login_failed:
            return cls.Status.LOGIN_FAILED
        else:
            return cls.Status.LOGGED_IN

    @classmethod
    def clear(cls) -> None:
        cls.session = None

    def __init__(self, handle=None, password=None):
        SskySession.login_internal(handle=handle, password=password)

    def persist(self) -> None:
        if SskySession.status() == SskySession.Status.NOT_LOGGED_IN:
            raise atproto_client.exceptions.LoginRequiredError('Login first')
        elif SskySession.status() == SskySession.Status.LOGIN_FAILED:
            pass
        else:
            SskySession.persist_internal()

    def client(self) -> atproto.Client:
        if SskySession.status() == SskySession.Status.NOT_LOGGED_IN:
            raise atproto_client.exceptions.LoginRequiredError('Login first')
        elif SskySession.status() == SskySession.Status.LOGIN_FAILED:
            pass
        else:
            return SskySession.session.client

    def profile(self) -> atproto_client.models.AppBskyActorDefs.ProfileViewDetailed:
        if SskySession.status() == SskySession.Status.NOT_LOGGED_IN:
            raise atproto_client.exceptions.LoginRequiredError('Login first')
        elif SskySession.status() == SskySession.Status.LOGIN_FAILED:
            pass
        else:
            return SskySession.session.profile

def ssky_client(login_handle=None, login_password=None) -> atproto.Client:
    return SskySession(handle=login_handle, password=login_password).client()

def ssky_profile(login_handle=None, login_password=None) -> atproto_client.models.AppBskyActorDefs.ProfileViewDetailed:
    return SskySession(handle=login_handle, password=login_password).profile()

def expand_actor(name: str, login_handle=None, login_password=None) -> str:
    profile = SskySession(handle=login_handle, password=login_password).profile()
    if profile is None:
        return None
    else:
        if name == 'myself':
            actor = profile.did
        else:
            actor = name
        return actor