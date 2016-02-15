"""Alerts module

Contains helper functions for keeping track of alert messages to show
to users. These alerts are intended to be used along with `Bootstrap's
Alert component <https://getbootstrap.com/components/#alerts>`_.

"""
from functools import wraps

from bottle import request


def load_alerts(func):
    """Updates a handler's returned template context by adding a list of
    alerts to be rendered by the template.

    The wrapped function must return a dict of template variables
    (i.e., a template context).

    It makes sense to use this decorator in conjunction with
    :func:`bottle.view`. By wrapping a handler with
    :func:`load_alerts` before wrapping it with :func:`bottle.view`,
    one can add alerts to the template context before trying to render
    the template.

    It **does** makes sense to use this decorator with ``HTTP GET``
    handlers.

    It **does not** make sense to use this decorator with ``HTTP
    POST`` handlers.

    :param: A handler function to wrap
    :returns: The wrapped function

    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = request.environ.get('beaker.session')
        alerts = session.get('alerts', [])
        context = func(*args, **kwargs)
        context['alerts'] = alerts
        session['alerts'] = []
        session.save()
        return context
    return wrapper


def save_alerts(*alerts, kind="danger"):
    """Saves alert messages to be later rendered on a template.

    Saves alerts for the user to a session cookie. Google it if you
    want.

    :param alerts: The alerts (each of type :class:`str`) to add to
        the alerts to show the user

    :param str kind: The kind of alert to use. Must be one of
        ``('success', 'warning', 'info', 'danger')``. This will be
        used to style the alert. See
        https://getbootstrap.com/components/#alerts.

    """
    kinds = ('success', 'warning', 'info', 'danger')
    if kind not in kinds:
        raise ValueError(
            "Invalid 'kind'. Must be one of {}, not '{}'.".format(kinds, kind)
        )
    session = request.environ.get('beaker.session')
    prev = session.get('alerts', [])
    session['alerts'] = prev + [{'message': a, 'kind': kind} for a in alerts]
    session.save()


def save_success(*alerts):
    """Saves a success message to be later rendered on a template.

    See :func:`alerts.save_alerts`.

    :param alerts: The alerts (each of type :class:`str`) to add to
        the alerts to show the user
    """
    return save_alerts(*alerts, kind="success")


def save_danger(*alerts):
    """Saves a danger message to be later rendered on a template.

    See :func:`alerts.save_alerts`.

    :param alerts: The alerts (each of type :class:`str`) to add to
        the alerts to show the user
    """
    return save_alerts(*alerts, kind="danger")
