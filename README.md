# ssky - Simple Bluesky client

## Introduction

Ssky is a simple Bluesky client, providing some specific features.

* Simple but Linux shell friendly user interface
  * You can give `URI` or `URI::CID` to retrieve (get), quote, reply-to, repost/unrepost and delete a unique post
  * You can give `DID` or `handle` to retrieve timeline/posts/profile, follow/unfollow a unique user
  * You can get simply 'URI:CID' for posts and 'DID' for users when you retrieve (get) them, so you can use them for Linux pipeline or command substitution
  * Various output options:
    * Only unique identifier such as `URI::CID` or `DID`, for Linux pipeline or command substitution ([See Samples](#samples) )
    * Line oriented output with identifier and human friendly text, for listing many records
    * Multiline output with full texts of some attributes, for reading details
    * JSON output, for preserving record structure derived from atproto library
    * Some subcommands such as `get` and `search` allow to output to files per records

### Requirements

* Python 3.12 or later

### Install from github repository

```bash
pip install ssky
```

## Quick Start

Ssky's behavior is specified by subcommand and options like `ssky subcommand [options]`.

### Common options and names

* Common option -D, --delimiter: Delimiter string in output
* Common option -I, --id: Identifier only such as `URI::CID` or `DID`, depending on context
* Common option -T, --text: Text only such as main text in post or description in user profile
* Common option -L, --long: Long output
* Common option -J, --json: JSON output
* Common option -N NUM, --limit NUM: MAX result counts
* Common option -O DIR, --output DIR: Output to files in the specified directory
* Common name "myself": replace with login user DID or handle automatically

### Login bluesky

First or all, you must log in the Bluesky.

```sh
ssky login handle password
```

*Handle* and *password* are formatted like `xxxx.bsky.social` and `xxxx-xxxxx-xxxx-xxxx`, respectively.

Once you have logged in, ssky remembers the login session in local environment (`~/.ssky`).
However, you must log in again when ssky reports session timeout error like "400 Token has been revoked".

You can also set Bluesky handle and password in environment variable `SSKY_USER`, separated by ':' like `handle:password`.

```sh
export SSKY_USER=user.bsky.social:xxxx-xxxxx-xxxx-xxxx
```

The environment variable overrides command line arguments, so you will login by the user alpha in the following example.

```sh
SSKY_USER=alpha:password1 ssky login bravo password2
```

### Get posts

Get subcommand retrieves your timeline, another author's feed by handle or `DID`, and a post by `URI` or `URI::CID`.

```sh
ssky get # Get your timeline
ssky get handle # Get other author's feed by handle, such as user.bsky.social
ssky get did:... # Get other author's feed by DID
ssky get at://... # Get a post specified by URI
```

### Get profile

Profile subcommand retrieves the user profile from handle or display name.

```sh
ssky profile user.bsky.social
ssky profile 'Display Name'
```

### Post

Post subcommand sends a post. You can give the message by command line argument or the standard input.  Tags, link cards, mentions, quotations, reply-to and attached images are available.

```sh
ssky post Hello # Post from command line text
echo Hello | ssky post # Post from /dev/stdin
ssky post 'Hello, #bluesky @atproto.com https://bsky.app/' # Post with tags, mentions, and embed link card
ssky post 'Hello, bluesky!' --image dir1/hello1.png --image dir2/hello2.png # Post with images
ssky post 'Hello, bluesky!' --quote at://... # Quote the post
ssky post 'Hello, bluesky!' --reply-to at://... # Reply to the post

ssky post Hello --dry # Dry run
```

### Search posts

Search subcommand searches posts.

```sh
ssky search foo # Search posts including 'foo'
ssky search foo --author handle # Search posts including 'foo' by the specified author
ssky search foo --since 20240101 --until 20241231 # Search posts including 'foo' in  the specified period
```

### Delete post

Delete subcommand deletes a post.

```sh
ssky delete at://... # Delete the post
```

### Repost to post

Repost subcommand reposts the post.

```sh
ssky repost at://... # Repost the post
```

### Unrepost to post

Repost subcommand deletes the repost to a post.

```sh
ssky unrepost at://... # Delete your repost to the specified post
```

### Search users

User subcommand searches users.

```sh
ssky user foo # Search users including 'foo' in handle name and description
```

### Follow user

Follow subcommand follows a user.

```sh
ssky follow handle # Follow the user
ssky follow did:.. # Follow the user
```

### Unfollow user

Unfollow subcommand deletes the follow to the user.

```sh
ssky unfollow handle # Unfollow the user
ssky unfollow did:.. # Unfollow the user
```

## Samples

### Search keyword 'bluesky' in your posts

```sh
ssky search bluesky --author myself
```

### Save your last post in the directory './log'

```sh
ssky post 'My very important posted message'
ssky get myself --limit 1 --text --output ./log
```

### Reply to the last post by myself

```sh
ssky post 'Reply!' --reply-to $(ssky get myself --limit 1 --id)
```

## License

[MIT License](LICENSE)

## Author

[SimpleSkyClient Project](https://github.com/simpleskyclient)
