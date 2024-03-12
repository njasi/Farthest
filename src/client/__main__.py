"""
Simple python farther client launcher
"""

import os
import logging
import argparse

# load in env file, u may want to change `override`
# I just have it cause vscode is being annoying
from dotenv import load_dotenv

load_dotenv(override=True)


from FartherClient import FartherClient, ClientNotFoundError, InvalidSecretError


# TODO client inits listening to commands &
#   - the stream interface
#   - client shld have idle screen as well or smth


parser = argparse.ArgumentParser(
    prog="FartherClient",
    description="Runs a simple python based client for farther",
    epilog="TODO fill in with more description",
)
parser.set_defaults(which="start-config")

sub_parsers = parser.add_subparsers(help="sub-command help")

# parser for start command
parser_start = sub_parsers.add_parser("start", help="Start the farther client")
parser_start.set_defaults(which="start")
parser_start.add_argument(
    "flag",
    type=str,
    help="Short name you want to use in commands to refrence your client.",
)
parser_start.add_argument(
    "title",
    type=str,
    help="The title for your client that will show in farther",
)
parser_start.add_argument(
    "-d",
    "--description",
    type=str,
    help="A short description of the client",
)
parser_start.add_argument(
    "-u",
    "--user",
    type=int,
    help="Farther user id",
)
parser_start.add_argument(
    "--private",
    type=bool,
    default=False,
    action=argparse.BooleanOptionalAction,
    help="False if users other than the owner should see this client and be able to interact with it",
)
parser_start.add_argument(
    "--persist",
    type=bool,
    default=False,
    action=argparse.BooleanOptionalAction,
    help=(
        "If this client should persist in the database after the client disconnects,"
        "only use if you plan to have this as a semi perm client. Setting this to true "
        "will ensure that your title/flag are reserved."
    ),
)
parser_start.add_argument(
    "-s",
    "--secret",
    type=str,
    default=".client_secret",
    required=False,
    help="Secret key to protect your client",
)


# too lazy to mess with flags + required args, so starting from config is a seperate command
parser_config = sub_parsers.add_parser(
    "start-config", help="Start the client using the config_client file."
)
parser_config.set_defaults(which="start-config")

# for killing persistant clients
parser_remove = sub_parsers.add_parser(
    "remove",
    help=(
        "remove your client from the farthest db (automatic if --persist is false,"
        " so you only need to do this if you want to remove your client from the"
        " database and used the presist option previously). "
    ),
)
parser_config.set_defaults(which="parser_remove")
parser_remove.add_argument(
    "flag",
    type=str,
    help="Short name you want to use in commands to refrence your client.",
)
parser_remove.add_argument(
    "-s",
    "--secret",
    type=str,
    default=".client_secret",
    required=False,
    help="Secret key to protect your client",
)


def start(args):
    """
    Start the farther client from the args provided
    """
    client = FartherClient(**args)
    client.launch()


def remove(args):
    client = FartherClient(**args)
    try:
        client.remove()
    except ClientNotFoundError:
        logging.warning(
            "The client to remove was not found in the database. Please check that you used the correct flag."
        )
    except InvalidSecretError:
        logging.warning("The provided secret is invalid")


# how argument vars map to env vars
ENV_MAPPINGS = {
    "flag": "CLIENT_FLAG",
    "title": "CLIENT_TITLE",
    "description": "CLIENT_DESCRIPTION",
    "owner_id": "CLIENT_OWNER_ID",
    "private": "CLIENT_PRIVATE",
    "persist": "CLIENT_PERSIST",
    "secret": "CLIENT_SECRET",
}


def load_env(mappings=ENV_MAPPINGS):
    """
    load the env vars into args as described in mappings
    """
    args = {}
    for key in mappings:
        args[key] = os.environ[mappings[key]]
    return args


if __name__ == "__main__":
    args = parser.parse_args()

    if args.which == "start-config":
        args.__dict__.update(load_env())

        start(args.__dict__)
    elif args.which == "start":
        start(args)
    elif args.which == "remove":
        remove(args)
