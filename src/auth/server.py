import datetime
import os

import jwt
from flask import Flask, request
from flask_mysqldb import MySQL


server = Flask(__name__)
mysql = MySQL(server)

# config
server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_PORT"] = int(os.environ.get("MYSQL_PORT"))
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")


@server.route("/login", methods=["POST"])
def login():
    """
    Takes an email and password and returns a JWT.
    """
    auth = request.authorization  # to get credentials (username and password) from Authorization header (i.e. Authorization: Basic <base64(username:password)>)
    if not auth:
        return "missing credentials", 401

    # check db for username and password
    cursor = mysql.connection.cursor()
    users_list = cursor.execute(
        "SELECT email, password FROM user WHERE email=%s", (auth.username,)
    )

    if users_list > 0:
        user_row = cursor.fetchone()
        email = user_row[0]
        password = user_row[1]

        if auth.username != email or auth.password != password:
            return "invalid credentials", 401
        else:
            return create_JWT(auth.username, os.environ.get("JWT_SECRET"), True)
    else:
        return "invalid credentials", 401


@server.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers["Authorization"]

    if not encoded_jwt:
        return "missing credentials", 401

    # Basic authentication scheme - Authorization: Basic <base64(username:password)>
    # JWT authentication scheme - Authorization: Bearer <JWT token>
    # for simplicity purposes, we'll assume that authorization header will contain a Bearer token (to avoid checking the
    # type of authentication - i.e. word that comes before credentials in the header ('Basic' or 'Bearer'))
    # in actual production environment, we'd need to check the type/authentication scheme present in Authorization header.

    encoded_jwt = encoded_jwt.split(" ")[1]  # Bearer <JWT token>

    try:
        decoded = jwt.decode(
            encoded_jwt,
            key=os.environ.get("JWT_SECRET"),
            algorithms=["HS256"]
        )
    # except jwt.DecodeError:
    except:
        return "invalid credentials", 403

    return decoded, 200


def create_JWT(username, secret, authz):  # authz is a boolean value telling us whether the user is an admin or not
    return jwt.encode(
        {
            "username": username,
            "exp": datetime.datetime.now(tz=datetime.timezone.utc)
                   + datetime.timedelta(days=1),
            "iat": datetime.datetime.utcnow(),
            "admin": authz  # if True, user will have access to all endpoints
        },
        key=secret,
        algorithm="HS256"
    )


if __name__ == "__main__":
    # host=0.0.0.0 is needed to make server publicly available - this tells OS to listen on all public APIs;
    # otherwise, it'll be accessible from localhost only (and localhost is only accessible within the host - outside requests
    # made to a Docker container will never make it to our Flask app)
    # each Docker container is given its own IP address (within the Docker network) which is used to send requests to that Docker container
    # we need to tell our Flask application to listen on our container's IP address so that our Flask application can receive
    # requests coming to this IP address
    # and container's IP address is subject to change, so '0.0.0.0' acts like a wildcard and tells our Flask application to
    # listen on any and all containers IP addresses
    # E.g. if we connect our Docker container to 2 separate Docker networks, Docker will assign a different IP address to
    # our container for each Docker network - but with 0.0.0.0 port configuration, Flask app will listen to requests coming
    # to both IP addresses assigned to the container
    server.run(host="0.0.0.0", port=5000)
