# RocketTalk

This project contains a Python program designed to help Team Rocket members communicate via "web mail" when other forms of communication have been compromised.
Documentation for its behavior can be found publicly here: http://cpl.mwisely.xyz
To verify that it works properly, your code must pass the provided tests.

**Note: Follow the design specifications EXACTLY.**
Not doing so will break the existing, complete test suite and hurt your grade.
Additionally, the provided HTML templates (which you should not edit) may not render properly.

**Note: the instructions provided below will work on campus machines. If you use your own machine, you are on your own.**

## Setting up a `virtualenv`

You will want to use a [virtualenv](https://virtualenv.pypa.io/en/stable/) for this project.

To set up your virtualenv, simply...

~~~shell
# Change into your project directory (i.e., the directory where this README lives)
$ cd # wherever your directory is

# Create a virtual environment **using the correct version of Python** and name it 'env'
$ virtualenv --python=$(which python3.4) env

# Run `ls` to verify that the env directory was created
$ ls
... requirements.txt env server.py  ...

# Enter the virtualenv
$ source env/bin/activate

# Notice that we have a little doodah at the front of our prompt that indicates
# that we're in the virtualenv now
(env) $

# Now we can install required Python packages
(env) $ pip install -r requirements.txt

# Whenever we're done working, we can run `deactivate` to exit the virtualenv...
(env) $ deactivate

# ...and our little indicator is gone.
$
~~~~

**Note:** DO **NOT** add your virtualenv to your git repository.

## Running Tests

Running `pip install -r requirements.txt` in your virtualenv will install pytest for you.
To run your tests, do the following:

~~~shell
# Activate your virtualenv (which is already setup and named "env")
$ source env/bin/activate
(env) $ py.test
~~~~

Note that you don't need a `./` this time.
virtualenv adds programs to your path when they are installed with `pip`.


By default, `py.test` should only collect the tests in `test_server.py`.
If it collects other stuff (like the stuff in `env/`), then simply run it as `py.test test_server.py` instead.
That way, it only collects the tests in that file.


## Checking Your Style

Running `pip install -r requirements.txt` in your virtualenv also installs flake8 for you.
To check your style with flake8, do the following:

~~~shell
# Activate your virtualenv (which is already setup and named "env")
$ source env/bin/activate
(env) $ flake8 *.py
~~~~

Note that you don't need a `./` this time.
virtualenv adds programs to your path when they are installed with `pip`.

## Running the Program

Running `pip install -r requirements.txt` in your virtualenv installs packages required to run your web application.
To run the web application, do the following:

~~~shell
# Activate your virtualenv (which is already setup and named "env")
$ source env/bin/activate
(env) $ python3.4 server.py --port=<portnumber>
~~~

... where `<portnumber>` is a port number of your choosing in the range `(8000, 9000]`.

[1]: http://docs.python-guide.org/en/latest/dev/virtualenvs/

<!--  LocalWords:  virtualenv
 -->
