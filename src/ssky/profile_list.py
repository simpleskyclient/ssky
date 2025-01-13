import os
from atproto_client import models
from ssky.ssky_session import SskySession
from ssky.util import summarize

class ProfileList:

    class Item:
        profile: models.AppBskyActorDefs.ProfileViewDetailed = None

        def __init__(self, profile: models.AppBskyActorDefs.ProfileViewDetailed) -> None:
            self.profile = profile

        def id(self) -> str:
            return self.profile.did

        def text_only(self) -> str:
            return self.profile.description if self.profile.description else ''

        def short(self, delimiter: str = None) -> str:
            if delimiter is None:
                delimiter = ProfileList.get_default_delimiter()
            did = self.profile.did
            handle = self.profile.handle
            display_name_summary = summarize(self.profile.display_name)
            description_summary = summarize(self.profile.description, length_max=40)
            return delimiter.join([did, handle, display_name_summary, description_summary])

        def long(self) -> str:
            description_summary = self.profile.description if self.profile.description else ''
            return '\n'.join([
                f'Created-At: {self.profile.created_at}',
                f'DID: {self.profile.did}',
                f'Display-Name: {self.profile.display_name}',
                f'Handle: {self.profile.handle}',
                '',
                f'{description_summary}'
            ])

        def json(self) -> str:
            return models.utils.get_model_as_json(self.profile)

        def printable(self, format: str, delimiter: str = None) -> str:
            if format == 'id':
                return self.id()
            elif format == 'long':
                return self.long()
            elif format == 'text':
                return self.text_only()
            elif format == 'json':
                return self.json()
            else:
                return self.short(delimiter=delimiter)

        def get_filename(self) -> str:
            filename = f"{self.profile.handle}.txt"
            return filename

    default_delimiter = ' '

    @classmethod
    def set_default_delimiter(cls, delimiter: str) -> None:
        cls.default_delimiter = delimiter

    @classmethod
    def get_default_delimiter(cls) -> str:
        return cls.default_delimiter

    def __init__(self, default_delimiter: str = None) -> None:
        self.actors = []
        self.items = None
        if default_delimiter is not None:
            self.default_delimiter = default_delimiter

    def __str__(self) -> str:
        return str(self.actors)

    def __len__(self) -> int:
        return len(self.actors)

    def __iter__(self) -> 'ProfileList':
        return iter(self.actors)

    def __next__(self) -> str:
        return next(self.actors)

    def __getitem__(self, index: int) -> str:
        return self.actors[index]

    def append(self, actor: str) -> 'ProfileList':
        self.actors.append(actor)
        return self

    def update(self) -> 'ProfileList':
        if self.items is None:
            self.items = []
            block_count = len(self.actors) // 25
            for i in range(block_count + 1):
                begin = i * 25
                end = (i + 1) * 25 if i < block_count else len(self.actors)
                if begin != end:
                    profiles = SskySession().client().get_profiles(self.actors[begin:end]).profiles
                    for profile in profiles:
                        self.items.append(self.Item(profile))
        return self

    def print(self, format: str, output: str = None, delimiter: str = None) -> None:
        self.update()
        if output:
            for item in self.items:
                filename = item.get_filename()
                path = os.path.join(output, filename)
                with open(path, 'w') as f:
                    f.write(item.printable(format, delimiter=delimiter))
                    f.write('\n')
        else:
            continued = False
            for item in self.items:
                if format == 'long':
                    if continued:
                        print('----------------')
                    else:
                        continued = True
                print(item.printable(format, delimiter=delimiter))