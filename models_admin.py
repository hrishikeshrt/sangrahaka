#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask-Admin Models
"""

from flask import flash, redirect, url_for, request
from flask_security import current_user

from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView

###############################################################################


class CustomAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.has_role('owner')

    def inaccessible_callback(self, name, **kwargs):
        flash("Unauthorized access.")
        return redirect(url_for('show_home', next=request.url))


class BaseModelView(ModelView):
    column_display_pk = True
    column_hide_backrefs = False
    can_export = True
    create_modal = True
    edit_modal = True

    def is_accessible(self):
        return current_user.has_role('owner')

    def inaccessible_callback(self, name, **kwargs):
        flash("Unauthorized access.")
        return redirect(url_for('show_home', next=request.url))


class UserModelView(BaseModelView):
    column_exclude_list = ('password', 'fs_uniquifier')
    column_searchable_list = ('username',)


class LabelModelView(BaseModelView):
    column_searchable_list = ('label', 'description')


###############################################################################
