"""Helper functions for pytest
"""
import os
import pytest
import shutil
import tempfile

import bottle


@pytest.fixture(autouse=True)
def cleandir(request):
    """Set up and change to a temporary directory to use for each test.

    When the test is complete, change back to the original directory
    and delete the temporary one.

    """
    original = os.getcwd()
    tmpdir = tempfile.mkdtemp()

    # Copy files over to the temporary directory
    os.mkdir(os.path.join(tmpdir, "messages"))
    shutil.copyfile(os.path.join(original, "passwords.json"),
                    os.path.join(tmpdir, "passwords.json"))
    shutil.copytree(os.path.join(original, "templates"),
                    os.path.join(tmpdir, "templates"))

    # Change over to the newly setup temporary directory
    os.chdir(tmpdir)

    # A callback to cleanup after we're done with the test
    def cleanup():
        shutil.rmtree(tmpdir)
        os.chdir(original)

    # Set the callback
    request.addfinalizer(cleanup)


@pytest.fixture(autouse=True)
def clear_template_cache(request):
    """Clears the template cache before each test."""
    bottle.TEMPLATES.clear()


@pytest.fixture(autouse=True)
def set_bottle_debug_mode(request):
    """Ensures that bottle is set to use debug mode."""
    bottle.debug(True)
