"""Message module

Helper functions for working with sent and received messages.

"""
import json
import os

from datetime import datetime
from glob import glob
from uuid import uuid4


DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
"""The format to use for message time stamps"""


def validate_message_form(form):
    """Validates a message form in the following ways:

    * Checks that the form contains a "to" key
    * Checks that the form contains a "subject" key
    * Checks that the form contains a "body" key
    * Checks that the value of "to" is not blank
    * Checks that the value of "subject" is not blank
    * Checks that the value of "body" is not blank

    :param bottle.FormsDict form: A submitted form; retrieved from
        :class:`bottle.request`

    :returns: A list of error messages. Returning the empty list
        indicates that no errors were found.

    """
    errors = []
    for k in ("to", "subject", "body"):  # Checking these 
        if k in form:
            if form[k] == "":
                errors.append("ERROR: Nothing entered in field", k)
        else:
            errors.append("ERROR: No", k, "key found in message!")
    return errors


def _load_message(message_filename):
    """Loads message data from a file.

    Messages stored as JSON-encoded objects. Message data is loaded
    and returned as dictionaries with the following attributes:

    * **id** (:class:`str`) - The ID of the message. The same as
      its filename. Note that we **do not** store the id in the
      file. It is derived from the file name and added to the loaded
      message before we return it.

    * **to** (:class:`str`) - The username of the message recipient

    * **from** (:class:`str`) - The username of the message sender

    * **subject** (:class:`str`) - The subject of the message

    * **body** (:class:`str`) - The body of the message

    * **time** (:class:`datetime.datetime`) - The time when the
      message was sent

    :param str message_filename: The path of the file that stores the
        JSON-encoded message data. The name of the file have the form
        ``<uuid>.json``, where ``<uuid>`` is a unique ID:
        https://en.wikipedia.org/wiki/Universally_unique_identifier

    :returns: A loaded message dict as described above

    """
    with open(message_filename) as raw_file:
        msg_data = json.load(raw_file)
    msg = {}  # Because this homework makes me salty

    # Using os, we split the filename from its path and extension.
    msg["id"] = os.path.splitext(os.path.basename(message_filename))[0]
    msg["time"] = datetime.strptime(msg_data["time"], DATE_FORMAT)
    
    # Filling in the rest of msg keys
    for k in ("to", "from", "subject", "body"):
        msg[k] = msg_data[k]
    return msg


def load_message(message_id):
    """Loads a single message from the ``messages/`` directory.

    Uses the ID of a message to construct a file path, and uses
    :func:`message._load_message` to load and return the message data.

    :returns: A single loaded message.

    """
    pathname = "../messages/" + message_id
    return _load_message(pathname)


def load_all_messages():
    """Loads all messages from the ``messages/`` directory.

    Uses :func:`message._load_message` and `glob.glob
    <https://docs.python.org/3.4/library/glob.html#glob.glob>`_ to
    create a new list of loaded messages. Messages are sorted
    according to their timestamp, so that the returned list starts
    with the most recent message and ends with the least recent.

    :returns: A list of loaded messages ordered by timestamp from
        most to least recent.

    """
    all_msg = glob.glob("../messages/*.json")
    msgs = []
    for i in all_msg:
        msgs.append(_load_message(i))
    return sorted(msgs, key=lambda x: x["time"])


def load_sent_messages(username):
    """Loads all messages from the ``messages/`` directory that were
    **sent** by the specified user.

    Uses :func:`message._load_message` and `glob.glob
    <https://docs.python.org/3.4/library/glob.html#glob.glob>`_ to
    create a new list of loaded messages. Messages are sorted
    according to their timestamp, so that the returned list starts
    with the most recent message and ends with the least recent.

    The returned list container *only* messages that were sent by the
    specified user.

    :param str username: The sender we're filtering for

    :returns: A list of loaded messages (sent by ``username``) ordered
        by timestamp from most to least recent.

    """
    return [m for m in load_all_messages() if m["from"] == username]


def load_received_messages(username):
    """Loads all messages from the ``messages/`` directory that were
    **received** by the specified user.

    Uses :func:`message._load_message` and `glob.glob
    <https://docs.python.org/3.4/library/glob.html#glob.glob>`_ to
    create a new list of loaded messages. Messages are sorted
    according to their timestamp, so that the returned list starts
    with the most recent message and ends with the least recent.

    The returned list container *only* messages that were received by
    the specified user.

    :param str username: The receiver we're filtering for

    :returns: A list of loaded messages (received by ``username``) ordered
        by timestamp from most to least recent.

    """
    return [m for m in load_all_messages() if m["to"] == username]

def send_message(message_dict):
    """Saves a message to the ``messages/`` directory.

    The message dict contains the following fields:

    * **to** (:class:`str`) - The username of the message recipient

    * **from** (:class:`str`) - The username of the message sender

    * **subject** (:class:`str`) - The subject of the message

    * **body** (:class:`str`) - The body of the message

    * **time** (:class:`str`) - The time the message was sent

    The saved file is named uniquely by generating a UUID with
    Python's built-in `uuid.uuid4()
    <https://docs.python.org/3.4/library/uuid.html#uuid.uuid4>`_
    function. We won't have to worry about accidentally overwriting
    files that way.

    The dictionary converted to a JSON-encoded string and saved to a
    file. The saved file has the name ``<uuid>.json`` (where
    ``<uuid>`` is a UUID) and is stored in the ``messages/``
    directory.

    :param dict message_dict: A dictionary containing message
        information as described above.

    :raises OSError: If there's a problem writing to the file. Files
        are opened for `exclusive creation.
        <https://docs.python.org/3.4/library/functions.html#open>`_

    :returns: None

    """
    filename = "../messages/" + uuid4() + ".json"
    msg = {}
    for k in ("to", "from", "subject", "body", "time"):
        msg[k] = message_dict[k]
    with open(filename, 'w') as msg_file:
        json.dump(msg, msg_file)
    return
