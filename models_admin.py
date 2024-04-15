#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask-Admin Models
"""

from flask import flash, redirect, url_for, request
from flask_security import current_user

from flask_admin import AdminIndexView
from flask_admin.contrib.sqla import ModelView

from constants import ROLE_OWNER

###############################################################################


class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.has_role(ROLE_OWNER)

    def inaccessible_callback(self, name, **kwargs):
        flash("You do not have permission to view this resource.", "error")
        return redirect(url_for("show_login", next=request.url))


class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.has_role(ROLE_OWNER)

    def inaccessible_callback(self, name, **kwargs):
        flash("You do not have permission to view this resource.", "error")
        return redirect(url_for("show_home"))


###############################################################################


class BaseModelView(SecureModelView):
    column_display_pk = True
    column_hide_backrefs = False

    can_export = True
    can_create = False
    can_edit = True
    can_delete = False

    create_modal = False
    edit_modal = True

    can_set_page_size = True

    def __init__(self, model, session, **kwargs):
        if self.form_excluded_columns:
            self.form_excluded_columns = list(self.form_excluded_columns)
        else:
            self.form_excluded_columns = []

        # if columns were excluded from the list view
        # exclude them from create / edit forms as well
        if self.column_exclude_list:
            for field in self.column_exclude_list:
                self.form_excluded_columns.append(field)

        # exclude relationships from showing up in the create / edit forms
        for relationship in model.__mapper__.relationships:
            self.form_excluded_columns.append(relationship.key)

        self.form_excluded_columns = tuple(self.form_excluded_columns)
        super().__init__(model, session, **kwargs)


###############################################################################


class UserModelView(BaseModelView):
    column_exclude_list = ('password', 'fs_uniquifier')
    column_searchable_list = ('username',)


class LabelModelView(BaseModelView):
    column_searchable_list = ('label', 'description')


class LexiconModelView(BaseModelView):
    column_searchable_list = ('lemma', 'transliteration')


class AnnotationModelView(BaseModelView):
    column_searchable_list = ("annotator_id",)


###############################################################################
