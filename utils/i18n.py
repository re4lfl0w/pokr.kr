from flask import current_app as cur_app, request
from flask.ext.babel import Babel, get_locale
from functools import wraps

from utils.nlp.utils.translit import translit


__all__ = ['PopongBabel']


class PopongBabel(Babel):

    def init_app(self, app):
        super(PopongBabel, self).init_app(app)

        self.localeselector(localeselector)

        # shortcuts
        app.babel = self
        app.LOCALES = self.list_translations() + ['en']

        # jinja filters
        app.jinja_env.filters['translit'] = filter_translit

        # context processor
        app.context_processor(inject_locales)


class InvalidLocaleError(Exception):
    pass


class NotInAppContextError(Exception):
    pass


@wraps
def babel_context(f):
    def decorated(*args, **kwargs):
        if not hasattr(cur_app, 'babel') or not hasattr(cur_app, 'LOCALES'):
            raise NotInAppContextError()

        f(*args, **kwargs)
    return decorated


@babel_context
def is_valid_locale(locale):
    return locale in cur_app.LOCALES


def assert_valid_locale(locale):
    if not is_valid_locale(locale):
        raise InvalidLocaleError()


def host(locale=None):
    assert_valid_locale(locale)

    bottom_level_domain, rest = request.host.split('.', 1)
    if not is_valid_locale(bottom_level_domain):
        host = request.host
    else:
        host = rest

    return '{locale}.{host}'.format(locale=locale, host=host)


@babel_context
def localeselector():
    locale, _ = request.host.split('.', 1)
    if not is_valid_locale(locale):
        locale = cur_app.babel.default_locale
    return locale


@babel_context
def inject_locales():
    # TODO: caching
    locale_links = {
            locale: request.url.replace(request.host, host(locale))
            for locale in cur_app.LOCALES
        }

    return dict(locale_links=locale_links,
            locale=str(get_locale()))

def filter_translit(*args, **kwargs):
    locale = str(get_locale())
    _type = kwargs.get('type')
    if len(args) == 1:
        string = args[0]
        return translit(string, 'ko', locale, _type) if locale != 'ko' else string
    elif args:
        raise Exception('filter_translit() only accepts one or zero argument')
    else:
        return lambda x: filter_translit(x, type=_type)
