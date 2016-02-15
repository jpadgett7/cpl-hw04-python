# Python standard library imports
import json
import os
import pickle
import random
import string
import time

from base64 import b64decode
from datetime import datetime
from glob import glob
from urllib.parse import urlsplit

# Other libraries
from webtest import TestApp as HelperApp  # To avoid confusing PyTest

# Our code
import server
import message


def assert_redirect_to_login(path):
    """A helper function to test that we're redirected if we're not
    logged in.

    """
    app = HelperApp(server.message_app)

    # Assert that we get redirected
    response = app.get(path)
    assert response.status == "302 Found"

    # Make sure the redirect is going to the right place
    assert urlsplit(response.location).path == "/login/"


def assert_not_redirect_to_login(path):
    """A helper function to test that we're not redirected if we're
    logged in.

    """
    app = HelperApp(server.message_app)

    # Login as Jessie
    app.post('/login/', {'username': 'jessie', 'password': 'frog'})

    # Assert that we're not redirected
    response = app.get(path)
    assert response.status == "200 OK"


def unpack_alerts(cookies):
    return pickle.loads(b64decode(cookies['beaker.session.id'][40:]))['alerts']


def test_message_structure():
    """Make sure that our saved messages contain the types we want."""
    app = HelperApp(server.message_app)
    app.post('/login/', {'username': 'jessie', 'password': 'frog'})

    # Add a bunch of messages
    for l in string.ascii_lowercase:
        app.get('/compose/')
        app.post('/compose/', {'to': 'james', 'subject': l, 'body': l.upper()})

    all_messages = message.load_all_messages()
    sent_messages = message.load_sent_messages('jessie')
    received_messages = message.load_sent_messages('james')

    # Check that we're loading messages correctly
    for messages in (all_messages, sent_messages, received_messages):
        for m in messages:
            # Check that our keys match up
            assert set(m) == {'id', 'from', 'to', 'subject', 'body', 'time'}

            # Check that load_all_messages loads the correct types
            assert isinstance(m['to'], str)
            assert isinstance(m['from'], str)
            assert isinstance(m['subject'], str)
            assert isinstance(m['body'], str)
            assert isinstance(m['time'], datetime)


def test_received_messages():
    """Make sure that we're filtering received messages properly."""
    app = HelperApp(server.message_app)
    # Get a list of people to send messages to (everyone who's not Jessie)
    with open("passwords.json") as f:
        passwords = json.load(f)
        people = set(passwords.keys())

    # Add a bunch of messages (26)
    for l in string.ascii_lowercase:
        sender = random.choice(list(people))
        receiver = random.choice(list(people - set(sender)))
        app.post('/login/', {'username': sender,
                             'password': passwords[sender]})

        app.get('/compose/')
        app.post('/compose/', {'to': receiver,
                               'subject': l, 'body': l.upper()})

    received = {}
    for person in people:
        messages = message.load_received_messages(person)
        received[person] = messages

        # It's extremely improbable that all of the messages would go to
        # the same person.
        assert len(messages) < 26

        for m in messages:
            assert m['to'] == person

    # We should have seen 26 total messages
    assert sum(len(l) for l in received.values()) == 26

    # We should have 26 unique messages
    assert len(set(x['id'] for l in received.values() for x in l)) == 26


def test_sent_messages():
    """Make sure that we're filtering received messages properly."""
    app = HelperApp(server.message_app)

    # Get a list of people to send messages to (everyone who's not Jessie)
    with open("passwords.json") as f:
        passwords = json.load(f)
        people = set(passwords.keys())

    # Add a bunch of messages (26)
    for l in string.ascii_lowercase:
        sender = random.choice(list(people))
        receiver = random.choice(list(people - set(sender)))
        app.post('/login/', {'username': sender,
                             'password': passwords[sender]})

        app.get('/compose/')
        app.post('/compose/', {'to': receiver,
                               'subject': l, 'body': l.upper()})

    sent = {}
    for person in people:
        messages = message.load_sent_messages(person)
        sent[person] = messages

        # It's extremely improbable that all of the messages would go to
        # the same person.
        assert len(messages) < 26

        for m in messages:
            assert m['from'] == person

    # We should have seen 26 total messages
    assert sum(len(l) for l in sent.values()) == 26

    # We should have 26 unique messages
    assert len(set(x['id'] for l in sent.values() for x in l)) == 26


def test_order_of_loaded_messages():
    """Make sure that load_messages maintains order for us."""
    app = HelperApp(server.message_app)
    app.post('/login/', {'username': 'jessie', 'password': 'frog'})

    # Add a bunch of messages
    for i, l in enumerate("abcd"):
        # Sleep a second so that our messages have different timestamps
        if i != 0:
            time.sleep(1)

        app.get('/compose/')
        app.post('/compose/', {'to': 'james', 'subject': l, 'body': l.upper()})

    all_messages = message.load_all_messages()
    sent_messages = message.load_sent_messages('jessie')
    received_messages = message.load_sent_messages('james')

    # Check that we're loading messages correctly
    for messages in (all_messages, sent_messages, received_messages):
        for prev, current in zip(messages, messages[1:]):
            assert prev['time'] > current['time']


def test_view_authorization():
    """Make sure that we can only view messages to/from us."""
    app = HelperApp(server.message_app)

    # Send a message from Jessie to James
    app.post('/login/', {'username': 'jessie', 'password': 'frog'})
    app.get('/compose/')
    app.post('/compose/', {'to': 'james', 'subject': 's', 'body': 'S'})

    # Find the message
    msg, = message.load_sent_messages('jessie')

    # Make sure Jessie can see it
    response = app.get('/view/{}/'.format(msg['id']))
    assert response.status == "200 OK"

    # Make sure James can see it
    app.get('/logout/')
    app.post('/login/', {'username': 'james', 'password': 'potato'})
    response = app.get('/view/{}/'.format(msg['id']))
    assert response.status == "200 OK"

    # Make sure Cassidy can't
    app.get('/logout/')
    app.post('/login/', {'username': 'cassidy', 'password': 'dog'})
    response = app.get('/view/{}/'.format(msg['id']))
    assert response.status == "302 Found"
    assert urlsplit(response.location).path == "/"


def test_compose_success_alerts():
    """Try adding an message and check for success messages."""
    app = HelperApp(server.message_app)
    app.post('/login/', {'username': 'jessie', 'password': 'frog'})

    # Clear alerts
    app.get('/')

    # Add a message
    app.post('/compose/', {'to': 'james', 'subject': "frog", 'body': "FROG!"})

    # Unpack the alerts from the session cookie, and assert that we
    # see the right message
    alerts = unpack_alerts(app.cookies)
    assert len(alerts) == 1, "Expected exactly one alert message"
    assert alerts == [{'kind': 'success',
                       'message': 'Message sent!'}]


def test_compose_missing_fields_alerts():
    """Check that we warn for missing fields"""
    app = HelperApp(server.message_app)
    app.post('/login/', {'username': 'jessie', 'password': 'frog'})

    # Clear alerts
    app.get('/')

    # Blank fields
    app.post('/compose/', {'to': '', 'subject': '', 'body': ''})

    # Make sure we warn
    alerts = unpack_alerts(app.cookies)
    assert len(alerts) == 3
    assert all(a['kind'] == 'danger' for a in alerts)
    assert set(a['message'] for a in alerts) == {
        'to field cannot be blank!',
        'subject field cannot be blank!',
        'body field cannot be blank!'
    }


def test_compose_form_validation():
    """Check that we warn for bad forms"""
    app = HelperApp(server.message_app)
    app.post('/login/', {'username': 'jessie', 'password': 'frog'})

    # Clear alerts
    app.get('/')

    # Missing fields
    app.post('/compose/', {'subjec': 'A', 'two': 'B', 'bodee': 'nope'})

    # Make sure we warn
    alerts = unpack_alerts(app.cookies)
    assert len(alerts) == 3
    assert all(a['kind'] == 'danger' for a in alerts)
    assert set(a['message'] for a in alerts) == {
        "Missing subject field!",
        "Missing to field!",
        "Missing body field!"
    }


def test_compose_files():
    """Try adding a bunch of messages, ensuring that files are created
    on disk.

    """
    app = HelperApp(server.message_app)
    app.post('/login/', {'username': 'jessie', 'password': 'frog'})

    for l in string.ascii_lowercase:
        app.get('/compose/')
        app.post('/compose/', {'to': 'james', 'subject': l, 'body': l.upper()})

    msg_filenames = glob("messages/*.json")
    assert len(msg_filenames) == 26

    letters = set()
    for msg_name in msg_filenames:
        with open(msg_name) as msg_file:
            msg_data = json.load(msg_file)

        # Assert that the set of keys is what we want
        assert set(msg_data) == {'body', 'subject', 'to', 'from', 'time'}

        # Since we're logged in as Jessie
        assert msg_data['from'] == 'jessie'

        # Check that we saved the subject and body correctly
        # (body is the uppercase version of subject)
        assert ord(msg_data['subject']) == ord(msg_data['body']) + 32

        # Remember all the letters we've seen so far
        letters.add(msg_data['subject'])

        # Make sure we can load the time correctly -- shouldn't throw
        # an exception
        datetime.strptime(msg_data['time'], "%Y-%m-%d %H:%M:%S")

    assert letters == set(string.ascii_lowercase)


def test_delete_success_alert():
    """Try removing an message, ensuring there's a success message"""
    app = HelperApp(server.message_app)
    app.post('/login/', {'username': 'jessie', 'password': 'frog'})

    # Add a an message
    app.post('/compose/', {'to': 'james', 'subject': 's', 'body': 'S'})
    app.get('/')        # Clears alerts

    # Delete something real
    msg_file, = glob("messages/*.json")
    msg_id = os.path.basename(msg_file).rstrip('.json')
    app.post('/delete/{}/'.format(msg_id))

    # Make sure we display a success message
    alerts = unpack_alerts(app.cookies)
    assert len(alerts) == 1
    assert alerts == [{'kind': 'success',
                       'message': 'Deleted {}.'.format(msg_id)}]


def test_delete_bogus_alert():
    """Try removing a bogus message, ensuring there's a warning"""
    app = HelperApp(server.message_app)
    app.post('/login/', {'username': 'jessie', 'password': 'frog'})

    # Add a message
    app.post('/compose/', {'to': 'james', 'subject': 's', 'body': 'b'})
    app.get('/')        # Clears alerts

    # Remove something bogus
    # Pick some arbitrary UUID. Collision is improbable.
    bogus_uuid = "b58cba44-da39-11e5-9342-56f85ff10656"
    app.post('/delete/{}/'.format(bogus_uuid))

    # Make sure we warn the user about it
    alerts = unpack_alerts(app.cookies)
    assert len(alerts) == 1
    assert alerts == [{'kind': 'danger',
                       'message': 'No such message {}'.format(bogus_uuid)}]


def test_delete():
    """Try adding a bunch of messages, and delete a couple items"""
    app = HelperApp(server.message_app)
    app.post('/login/', {'username': 'jessie', 'password': 'frog'})

    for l in string.ascii_lowercase:
        app.post('/compose/', {'to': 'james', 'subject': l, 'body': l.upper()})

    # We should have all 26
    assert len(glob("messages/*.json")) == 26

    for msg_name in glob("messages/*.json"):
        msg_id = os.path.basename(msg_name).rstrip('.json')

        # The file should be in there
        assert msg_name in glob("messages/*.json")

        # Get the form (to make sure it doesn't change anything on disk)
        app.get('/delete/{}/'.format(msg_id))

        # The file should still be in there
        assert msg_name in glob("messages/*.json")

        # Try to delete it
        app.post('/delete/{}/'.format(msg_id))

        # The file should be gone
        assert msg_name not in glob("messages/*.json")

    # Ain't nothin' left, I'll tell ya what.
    assert len(glob("messages/*.json")) == 0


def test_shred_success_alert():
    """Try shreding messages, ensuring there's a success message"""
    app = HelperApp(server.message_app)
    app.post('/login/', {'username': 'jessie', 'password': 'frog'})

    # Add a an message
    app.post('/compose/', {'to': 'james', 'subject': 's', 'body': 'b'})
    app.get('/')        # Clears alerts

    # Remove something bogus
    app.post('/shred/')

    # Make sure we warn the user about it
    alerts = unpack_alerts(app.cookies)
    assert len(alerts) == 1
    assert alerts == [{'kind': 'success',
                       'message': 'Shreded all messages.'}]


def test_shred():
    """Try adding a bunch of messages, and clear them out"""
    app = HelperApp(server.message_app)
    app.post('/login/', {'username': 'jessie', 'password': 'frog'})

    for l in string.ascii_lowercase:
        app.post('/compose/', {'to': 'james', 'subject': l, 'body': l.upper()})

    # We should have all 26
    assert len(glob("messages/*.json")) == 26

    # This shouldn't change the files
    app.get('/shred/')

    # We should still have all 26
    assert len(glob("messages/*.json")) == 26

    # Delete all the message files
    app.post('/shred/')

    # OK, now they're gone.
    assert len(glob("messages/*.json")) == 0


def test_list_login():
    """Make sure we get redirected as expected for /"""
    assert_redirect_to_login('/')
    assert_not_redirect_to_login('/')


def test_compose_login():
    """Make sure we get redirected as expected for /compose/"""
    assert_redirect_to_login('/compose/')
    assert_not_redirect_to_login('/compose/')


def test_delete_login():
    """Make sure we get redirected as expected for /delete/"""
    # Pick some arbitrary UUID.
    uuid = "b58cba44-da39-11e5-9342-56f85ff10656"
    assert_redirect_to_login('/delete/{}/'.format(uuid))

    # We would get redirected to '/', since the UUID above is junk
    # assert_not_redirect_to_login('/delete/{}/'.format(uuid))


def test_shred_login():
    """Make sure we get redirected as expected for /shred/"""
    assert_redirect_to_login('/shred/')
    assert_not_redirect_to_login('/shred/')


def test_login_form_alerts():
    """Make sure login forms are validated"""
    app = HelperApp(server.message_app)

    # Use bad field names
    response = app.post('/login/', {'usernam': 'carmon', 'passwor': 'frog'})
    assert response.status == "302 Found"
    assert urlsplit(response.location).path == "/login/"

    # Check for alerts
    alerts = unpack_alerts(app.cookies)
    assert len(alerts) == 2
    assert all(a['kind'] == 'danger' for a in alerts)
    assert set(a['message'] for a in alerts) == {
        'Missing username field!',
        'Missing password field!'
    }

    # Clear EVERYTHING (including alerts)
    app.reset()

    # Use blank field names
    response = app.post('/login/', {'username': '', 'password': ''})
    assert response.status == "302 Found"
    assert urlsplit(response.location).path == "/login/"

    # Check for alerts
    alerts = unpack_alerts(app.cookies)
    assert len(alerts) == 2
    assert all(a['kind'] == 'danger' for a in alerts)
    assert set(a['message'] for a in alerts) == {
        'username field cannot be blank!',
        'password field cannot be blank!'
    }


def test_login():
    """Make sure login works as we expect"""
    app = HelperApp(server.message_app)

    # The page loads up
    response = app.get('/login/')
    assert response.status == "200 OK"

    # Doesn't work with a bad username
    response = app.post('/login/', {'username': 'carmon', 'password': 'frog'})
    assert response.status == "302 Found"
    assert urlsplit(response.location).path == "/login/"
    assert app.cookies.get('logged_in_as') is None

    # Doesn't work with a bad password
    response = app.post('/login/', {'username': 'jessie', 'password': 'fwog'})
    assert response.status == "302 Found"
    assert urlsplit(response.location).path == "/login/"
    assert app.cookies.get('logged_in_as') is None

    # Doesn't work with arbitrary password capitalization
    response = app.post('/login/', {'username': 'jessie', 'password': 'FROG'})
    assert response.status == "302 Found"
    assert urlsplit(response.location).path == "/login/"
    assert app.cookies.get('logged_in_as') is None

    # Works with a good password
    response = app.post('/login/', {'username': 'jessie', 'password': 'frog'})
    assert response.status == "302 Found"
    assert urlsplit(response.location).path == "/"
    assert app.cookies['logged_in_as'] == "jessie"

    # Works with various username capitalization
    response = app.post('/login/', {'username': 'Jessie', 'password': 'frog'})
    assert response.status == "302 Found"
    assert urlsplit(response.location).path == "/"
    assert app.cookies['logged_in_as'] == "jessie"


def test_logout():
    """Make sure logout works as we expect"""
    app = HelperApp(server.message_app)
    response = app.post('/login/', {'username': 'jessie', 'password': 'frog'})
    assert response.status == "302 Found"
    assert urlsplit(response.location).path == "/"
    assert app.cookies['logged_in_as'] == "jessie"

    response = app.get('/logout/')
    assert response.status == "200 OK"
    assert app.cookies['logged_in_as'] == ""
