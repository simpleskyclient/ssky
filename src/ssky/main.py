import argparse
from importlib import import_module
from importlib.metadata import version, PackageNotFoundError
import io
from operator import attrgetter
import os
import signal
import sys

def get_version():
    """Get the version of the ssky package."""
    try:
        return version("ssky")
    except PackageNotFoundError:
        return "unknown"

def parse():
    class SortingHelpFormatter(argparse.HelpFormatter):
        def add_arguments(self, actions):
            actions = sorted(actions, key=attrgetter('option_strings'))
            super(SortingHelpFormatter, self).add_arguments(actions)

    parser = argparse.ArgumentParser(formatter_class=SortingHelpFormatter, description='Simple Bluesky Client')
    parser.add_argument('--version', action='version', version=get_version())
    sp = parser.add_subparsers(dest='subcommand', title='Subcommand', required=True)

    delimiter_options = argparse.ArgumentParser(add_help=False)
    delimiter_options.add_argument('-D', '--delimiter', type=str, default=' ', metavar='STRING', help='Delimiter')

    format_options = argparse.ArgumentParser(add_help=False)
    format_options.add_argument('-O', '--output', type=str, default=None, metavar='DIR', help='Output to files')
    format_options.set_defaults(format='')
    format_options_group = format_options.add_mutually_exclusive_group()
    format_options_group.add_argument('-I', '--id', action='store_const', dest='format', const='id', help='Print identifier only')
    format_options_group.add_argument('-J', '--json', action='store_const', dest='format', const='json', help='Print in JSON format')
    format_options_group.add_argument('-L', '--long', action='store_const', dest='format', const='long', help='Print in long format')
    format_options_group.add_argument('-S', '--simple-json', action='store_const', dest='format', const='simple_json', help='Print in simplified JSON format for MCP')
    format_options_group.add_argument('-T', '--text', action='store_const', dest='format', const='text', help='Print text only')

    limit_options = argparse.ArgumentParser(add_help=False)
    limit_options.add_argument('-N', '--limit', type=int, metavar='NUM', help='Limit lines')

    delete_parser = sp.add_parser('delete', formatter_class=SortingHelpFormatter, help='Delete post')
    delete_parser.add_argument('post', type=str, help='URI(at://...)[::CID]')

    follow_parser = sp.add_parser('follow', formatter_class=SortingHelpFormatter, parents=[delimiter_options, format_options], help='Follow')
    follow_parser.add_argument('name', type=str, help='Handle, DID, or "myself" to follow')

    get_parser = sp.add_parser('get', formatter_class=SortingHelpFormatter, parents=[delimiter_options, format_options, limit_options], help='Get posts')
    get_parser.add_argument('target', nargs='?', type=str, default=None, metavar='PARAM', help='URI(at://...), DID(did:...), handle, "myself", or none as timeline')

    login_parser = sp.add_parser('login', formatter_class=SortingHelpFormatter, parents=[delimiter_options, format_options], help='Login')
    login_parser.add_argument('credentials', nargs='?', type=str, default=None, help='User credentials (handle:password)')

    post_parser = sp.add_parser('post', formatter_class=SortingHelpFormatter, parents=[delimiter_options, format_options], help='Post a message to the timeline')
    post_parser.add_argument('message', nargs='?', type=str, help='The message to post')
    post_parser.add_argument('-d', '--dry', action='store_true', help='Dry run')
    post_parser.add_argument('-i', '--image', action='append', type=str, default=[], metavar='PATH', help='Image files to attach')
    post_parser.add_argument('-q', '--quote', type=str, default=None, metavar='URI', help='Quote a post')
    post_parser.add_argument('-r', '--reply-to', type=str, default=None, metavar='URI', help='Reply to a post')

    profile_parser = sp.add_parser('profile', formatter_class=SortingHelpFormatter, parents=[delimiter_options, format_options], help='Show profile')
    profile_parser.add_argument('name', type=str, help='Handle, DID, or "myself" to show')

    repost_parser = sp.add_parser('repost', formatter_class=SortingHelpFormatter, parents=[delimiter_options, format_options], help='Repost')
    repost_parser.add_argument('post', type=str, help='URI(at://...)[::CID]')

    search_parser = sp.add_parser('search', formatter_class=SortingHelpFormatter, parents=[delimiter_options, format_options, limit_options], help='Search posts')
    search_parser.add_argument('q', nargs='?', type=str, default='*', metavar='QUERY', help='Query string')
    search_parser.add_argument('-a', '--author', type=str, default=None, metavar='ACTOR', help='Author handle, DID, or "myself"')
    search_parser.add_argument('-s', '--since', type=str, default=None, metavar='TIMESTAMP', help='Since timestamp (ex. 2001-01-01T00:00:00Z, 20010101000000, 20010101, "today", "yesterday")')
    search_parser.add_argument('-u', '--until', type=str, default=None, metavar='TIMESTAMP', help='Until timestamp (ex. 2099-12-31T23:59:59Z, 20991231235959, 20991231, "today", "yesterday")')

    unfollow_parser = sp.add_parser('unfollow', formatter_class=SortingHelpFormatter, parents=[delimiter_options, format_options], help='Unfollow')
    unfollow_parser.add_argument('name', type=str, help='Handle, DID, or "myself" to unfollow')

    unrepost_parser = sp.add_parser('unrepost', formatter_class=SortingHelpFormatter, parents=[delimiter_options, format_options], help='Unrepost a post')
    unrepost_parser.add_argument('post', type=str, help='URI(at://...)[::CID]')

    user_parser = sp.add_parser('user', formatter_class=SortingHelpFormatter, parents=[delimiter_options, format_options, limit_options], help='Search users')
    user_parser.add_argument('q', type=str, metavar='QUERY', help='Query string')

    args = parser.parse_args()
    subcommand = args.subcommand
    del args.subcommand

    return subcommand, args

def execute(subcommand, args) -> bool:
    try:
        module = import_module(f'.{subcommand}', f'{__package__}')
        func = getattr(module, f'{subcommand}')
        result = func(**vars(args))

        if result is None:
            return False
        else:
            from ssky.post_data_list import PostDataList
            from ssky.profile_list import ProfileList
            from ssky.util import ErrorResult
            
            if isinstance(result, ErrorResult):
                # Error result - return failure status, output already printed by function
                return False
            elif type(result) is PostDataList or type(result) is ProfileList:
                result.print(format=args.format, output=args.output, delimiter=args.delimiter)
            elif type(result) is list:
                if type(result[0]) is list:
                    for item in result:
                        print(args.delimiter.join(filter(lambda s: s is not None, item)))
                else:
                    print(args.delimiter.join(filter(lambda s: s is not None, result)))
            else:
                print(result)
            return True
    except ImportError as e:
        print(f'Module or function not found: {__package__}.{subcommand}', file=sys.stderr)
        print(e, file=sys.stderr)
        return False
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return False
    except Exception as e:
        print(str(e), file=sys.stderr)
        return False

def setup():
    signal.signal(signal.SIGINT, lambda num, frame: sys.exit(1))
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=False)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=False)

def main() -> int:
    setup()
    subcommand, args = parse()
    status = execute(subcommand, args)
    return 0 if status is True else 1

if __name__ == '__main__':
    sys.exit(main())