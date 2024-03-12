import bcrypt
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Clients(Base):
    """
    Client db table for tracking the active clients
        - web clients are not counted rn, just the python ones


    id:             int, unique id for the client item
    title:          string, the title of the client
    description:    string, a short description of the client
    flag:           string, shortname to refrence the client by in commands
    active:         bool, if the client is currently online
    addr:           string, the ip address of the client
    secret:         string, 'secret' key so only the owner can make changes to their client, user specified
                    yeah im storing this in plaintext, this aint important info
    public:         bool, if the client is public; FALSE => only owner can interact
    persist:        bool, if the client should always exist, ie main farther, etc (wont remove on disconnect)
    owner_id:       int, user id of the client owner
    """

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)

    # basic info
    title = Column(String)
    description = Column(String)

    # flag should be unique and always populated
    flag = Column(String, unique=True)
    active = Column(Boolean, default=True)

    # connection info
    addr = Column(String)
    secret = Column(String)

    # settings
    public = Column(Boolean, default=False)
    persist = Column(Boolean, default=False)

    # relationships
    #   - Client is owned by one user
    owner = relationship("Users")
    owner_id = Column(Integer, ForeignKey("users.id"))

    @secret.setter
    def secret(self, plaintext_password):
        # automatically hash the secret when set. It's not vital at all that it's secure,
        # but its trivial as u can see
        hashed = bcrypt.hashpw(plaintext_password.encode("utf-8"), bcrypt.gensalt())
        self.secret = hashed.decode("utf-8")

    def verify_secret(self, secret):
        bcrypt.checkpw(secret.encode("utf-8"), self.secret.encode("utf-8"))

    def __str__(self):
        """
        General case __str__ method cause im tired of memory addrs in debug
        """
        res = f"{type(self).__name__}("
        # add attrs to ignore here
        ignore = []

        columns = [m.key for m in self.__table__.columns]

        for key in columns:
            if key not in ignore:
                res += f"\n\t{key} = {getattr(self, key)}"
        res += ")\n"
        return res
