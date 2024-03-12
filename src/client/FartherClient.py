from VideoClient import VideoClient
from secret import ensure_secret


class InvalidSecretError(Exception):
    """
    Raised when the client tries to talk to the server,
    but the secret does not match
    """


class ClientNotFoundError(Exception):
    """
    Client could not be found on the server
    """


class FartherClient:
    """
    Class to manage:
        - channel settings & register wth server
        - worker thread (listen to socket and do commands)
        - cli interface?
    """

    def __init__(
        self,
        flag,
        title=None,
        description=None,
        addr=None,
        secret=".client_secret",
        private=False,
        persist=False,
        owner_id=None,
        **kwargs
    ):
        """
        Create a new client

        title:          string, the title of the client
        flag:           string, shortname to refrence the client by in commands
        description:    string, a short description of the client
        addr:           string, the ip address of the client (server will populate this but you can specify if needed)
        secret:         str, path to secret key for this client default (relative to project root)
                        default to .client_secret
        private:        bool, if the client should be private; FALSE => only owner can interact
        persist:        bool, if the client should always exist, ie main farther, etc (wont remove on disconnect)
                        if False the client will be removed from the db on disconnect
                        if True the client will stay in the db on disconnect for the next time you connect
        owner_id:       int, user id of the client owner (use /me on the farther telegram bot to get your id)
        """
        self.title = title
        self.flag = flag
        self.description = description
        self.addr = addr
        self.private = private
        self.persist = persist
        self.owner_id = owner_id

        self.secret = ensure_secret(secret)

        # for storing the worker thread for ref
        self.worker = None

        # the video client which plays the stream
        self.video: VideoClient = None

    def register(self):
        """
        Register the client with the server
        """
        # TODO

    def update():
        """
        Ask the server to update some values
        """
        # TODO

    def remove(self):
        """
        Ask the server to remove the client from the db
        """
        # TODO

    def launch(self):
        """
        Start the client
            - register with the server
            - start worker thread
            - launch cli
        """
        self.register()
        # TODO start worker thread

    def listen(self):
        pass
