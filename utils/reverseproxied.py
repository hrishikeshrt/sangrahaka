#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 10 13:56:54 2019

@author: Hrishikesh Terdalkar

# Solution for Different Mountpoint of Flask App
# https://github.com/alex-leonhardt/flask-blog/blob/master/reverseproxied.py
# https://gist.github.com/flengyel/1444972/f8338b7fa63475a23abf63c9a3fc68184791e8d2
# https://stackoverflow.com/questions/30743696/create-proxy-for-python-flask-application
# https://blog.macuyiko.com/post/2016/fixing-flask-url_for-when-behind-mod_proxy.html
"""

from werkzeug.middleware.proxy_fix import ProxyFix

###############################################################################


class ReverseProxied(object):
    '''Wrap the application in this middleware and configure the
    front-end server to add these headers, to let you quietly bind
    this to a URL other than / and to an HTTP scheme that is
    different than what is used locally.

    App is first wrapped in `ProxyFix()` middleware so that it gets a correct
    IP address of the requester

    In nginx:
    location /myprefix {
        proxy_pass http://127.0.0.1:5001;
        proxy_redirect off;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Script-Name /myprefix;

        # proxy_cookie_path / /myprefix;
    }

    If you need to run multiple instances of the application under the same
    domain at different subdomains, uncomment the `proxy_cookie_path` line

    :param app: the WSGI application
    '''
    def __init__(self, app, script_name=None, scheme=None, server=None, mounts=None):
        self.app = ProxyFix(app)
        self.script_name = script_name
        self.scheme = scheme
        self.server = server
        self.mounts = mounts or {}

    def __call__(self, environ, start_response):
        script_name = environ.get('HTTP_X_SCRIPT_NAME', '') or self.script_name
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        scheme = environ.get('HTTP_X_SCHEME', '') or self.scheme
        if scheme:
            environ['wsgi.url_scheme'] = scheme
        server = environ.get('HTTP_X_FORWARDED_SERVER', '') or self.server
        if server:
            environ['HTTP_HOST'] = server

        if self.mounts:
            subpath_info = environ.get("PATH_INFO", "")
            subpath_info_splits = subpath_info.split('/')
            if len(subpath_info_splits) > 1:
                app_path = '/%s' % subpath_info_splits[1]
                app_path_info = '/%s' % '/'.join(subpath_info_splits[2:])
            else:
                app_path = '/'
                app_path_info = '/'

            if app_path in self.mounts:
                app = self.mounts[app_path]
                environ['PATH_INFO'] = app_path_info
                environ['SCRIPT_NAME'] += app_path
            else:
                app = self.app
        else:
            app = self.app

        return app(environ, start_response)


###############################################################################
