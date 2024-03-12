"""
Simple module to generate / load / save a private-public
keypair
"""

import os
import base64
import secrets
import logging


def generate_secret():
    """
    Generate a random 32-byte API key & encode the bytes in base64
    """
    secret_bytes = secrets.token_bytes(64)
    return base64.b64encode(secret_bytes).decode("utf-8")


def relative_path(filename=".client_secret"):
    """
    Make a path to a file which is relative to the project's root
    """
    script_directory = os.path.dirname(os.path.abspath(__file__))
    output_directory = os.path.join(script_directory, "../../")

    # Create the full path to the output file
    return os.path.join(output_directory, filename)


def ensure_secret(file):
    """
    if needed generate a new secret key file, otherwise just read it

    in both cases return the secret key value
    """

    # if it exists just read it
    path = relative_path(filename=file)
    if os.path.exists(path):
        with open(path, "r") as file:
            secret = file.read()

            # dont allow empty string secret, pass by and generate new below
            if not secret == "":
                return secret

    # otherwise we want to generate a new key
    with open(path, "w") as file:
        logging.info("No secret key found, generating a new one.")
        secret = generate_secret()
        # security™
        logging.info(f"Generated new secret: {secret}")
        file.write(secret)
        return secret
