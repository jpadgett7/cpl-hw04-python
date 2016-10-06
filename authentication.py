"""Authentication module

Contains helper functions for checking whether a user is logged in.

"""
import json
from functools import wraps

from bottle import request, redirect

from alerts import save_danger
from message import load_message


def requires_authentication(func):
    """Updates a handler, so that a user is redirected to ``/login/`` if
    they are not currently logged in. If they **are** currently logged
    in, then proceed as usual.

    The wrapped function should be a handler function. When a user
    attempts to browse to the path for the wrapped handler, this
    wrapper will check to see if the user is logged in...

    * If the ``"logged_in_as"`` cookie is missing or blank, then the
      user is not logged in. As a result, they are redirected to
      ``/login/`` using :func:`bottle.redirect`.

    * Otherwise, the wrapped handler is called as usual, and the
      wrapper returns the value that was returned by the call to the
      wrapped handler.

    :param func: A handler function to wrap
    :returns: The wrapped function

    """
    @wraps(func)
    def gift_wrap(*args, **kwargs):  # A festive wrapper
        if not request.get_cookie("logged_in_as"):  # empty username
            redirect("/login/")
        else:  # all clear!
            return func(*args, **kwargs)
    return gift_wrap  # Happy holidays... oh, I'm early, aren't I?


def requires_authorization(func):
    """Updates a handler, so that a logged-in user is redirected when they
    attempt to access messages that do not belong to them.

    The wrapped function should be a handler function. When a user
    attempts to browse to the path for the wrapped handler, this
    wrapper will...

    * Look up the user's username by checking the "logged_in_as"
      cookie. If it is missing or blank, then the user is immediately
      redirected to ``/login/`` using :func:`bottle.redirect`, so that
      they may login.

    * If they are logged in, the message corresponding to the
      ``message_id`` is loaded using :func:`message.load_message`.

        * If :func:`message.load_message` raises an :class:`OSError`,
          a danger alert is saved, and the user is redirected to
          ``/``.

    * Then, we check that the loaded message was either sent **to**
      the current user, or sent **from** the current user.

        * If the user neither sent nor received the message, then a
          danger alert is saved, and the user is redirected to ``/``.

    * Otherwise, we can assume that the user is logged in, and does
      have access to the message. The wrapped handler is called as
      usual, and the wrapper returns the value that was returned by
      the call to the wrapped handler.

    **Note**: This decorator expects the first argument of the wrapped
    handler to be a message ID. Reading between the lines, the URL
    path should contain a single wildcard that corresponds with a
    message UUID.

    For example:

        @get('/some/kind/of_path/<message_id:re:[0-9a-f\-]{36}>/')
        def my_handler(message_id):
            # stuff

    You can read more about dynamic routes `on bottle's
    documentation<http://bottlepy.org/docs/dev/tutorial.html#dynamic-routes>`_

    :param func: A handler function to wrap
    :returns: The wrapped function

    """
    @wraps(func)
    def wrapper(m_id, *args, **kwargs):
        username = request.get_cookie("logged_in_as")
        if not username:  # i.e. username cookie is blank or empty
            redirect("/login/")
        else:  # user is logged in
            try:
                msg = load_message(m_id)
                if msg["to"] == username or msg["from"] == username:
                    return func(m_id, *args, **kwargs)  # all clear!
                else:  # User is not sender or recepient of message
                    save_danger("User not authorized to view message")
            except OSError:
                save_danger("Unable to load message")
                redirect("/")
    return wrapper


def validate_login_form(form):
    """Validates a login form in the following ways:

    * Checks that the form contains a "username" key
    * Checks that the form contains a "password" key
    * Checks that the value for "username" is not blank
    * Checks that the value for "password" is not blank

    :param bottle.FormsDict form: A submitted form; retrieved from
        :class:`bottle.request`

    :returns: A list of error messages. Returning the empty list
        indicates that no errors were found.

    """
    errors = []
    for k in ("username", "password"):
        if k in form:
            if form[k] == "":
                errors.append(k, "field cannot be blank!")
        else:
            errors.append("Missing", k, "field!")
    return errors


def check_password(username, password):
    """Checks a user's password using a plaintext password file.

    Opens a file named ``"passwords.json"``, and loads the
    JSON-formatted data using the built-in Python module ``json``.

    * Usernames are case insensitive.

    * Note that all usernames in "passwords.json" are stored in
      lowercase.

    :param str username: The username to check
    :param str password: The password to check

    :returns: True if the username/password pair was in
        "passwords.json", otherwise False

    """
    with open("passwords.json") as very_secure_docs:
        pw_list = json.load(very_secure_docs)
    if username in pw_list:
        return pw_list[username] == password
    else:
        return False
