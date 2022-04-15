#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Mar 07 13:08:36 2021

@author: Hrishikesh Terdalkar
"""

###############################################################################

from datetime import datetime as dt
from sqlalchemy import (Boolean, DateTime, Column, Integer, String, Text,
                        ForeignKey, JSON, Enum, Index)
from sqlalchemy.orm import relationship, backref


from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore
from flask_security.forms import LoginForm, RegisterForm, StringField, Required

###############################################################################
# Create database connection object

db = SQLAlchemy()

###############################################################################
# Corpus Database Models


class Corpus(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    scheme = Column(
        Enum('devanagari', 'velthuis', 'iast', 'slp1', 'hk'),
        default='devanagari', nullable=False
    )
    description = Column(String(255), nullable=False)


class Chapter(db.Model):
    id = Column(Integer, primary_key=True)
    corpus_id = Column(Integer, ForeignKey('corpus.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)

    corpus = relationship('Corpus',
                          backref=backref('chapters', lazy='dynamic'))


class Verse(db.Model):
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey('chapter.id', ondelete='CASCADE'),
                        nullable=False, index=True)

    chapter = relationship('Chapter',
                           backref=backref('verses', lazy='dynamic'))


class Line(db.Model):
    id = Column(Integer, primary_key=True)
    verse_id = Column(Integer, ForeignKey('verse.id', ondelete='CASCADE'),
                      nullable=False, index=True)
    text = Column(Text, nullable=False)
    split = Column(Text, nullable=False)

    verse = relationship('Verse', backref=backref('lines', lazy='dynamic'))


class Analysis(db.Model):
    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, ForeignKey('line.id', ondelete='CASCADE'),
                     nullable=False, index=True)
    source = Column(String(255), nullable=False)
    text = Column(Text, nullable=False)
    parsed = Column(JSON, nullable=False)

    line = relationship('Line', backref=backref('analyses', lazy='dynamic'))
    __table_args__ = (
        Index('analysis_line_id_source', 'line_id', 'source', unique=True),
    )

###############################################################################
# User Database Models


DEFAULT_SETTING = {
    'display_name': '',
    'theme': 'united',
}


class Role(db.Model, RoleMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    description = Column(String(255))
    level = Column(Integer)
    permissions = Column(String(255))


class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))
    active = Column(Boolean, default=True)
    fs_uniquifier = Column(String(255), unique=True)
    confirmed_at = Column(DateTime)
    settings = Column(JSON, default=DEFAULT_SETTING)
    last_login_at = Column(DateTime)
    current_login_at = Column(DateTime)
    last_login_ip = Column(String(255))
    current_login_ip = Column(String(255))
    login_count = Column(Integer)
    roles = relationship('Role', secondary='roles_users',
                         backref=backref('users', lazy='dynamic'))


class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('user.id'))
    role_id = Column('role_id', Integer, ForeignKey('role.id'))

###############################################################################
# Annotation Database Models


class Lexicon(db.Model):
    id = Column(Integer, primary_key=True)
    lemma = Column(String(255), unique=True)
    transliteration = Column(Text)


class NodeLabel(db.Model):
    __tablename__ = 'node_label'
    id = Column(Integer, primary_key=True)
    label = Column(String(255), nullable=False)
    description = Column(String(255))
    is_deleted = Column(Boolean, default=False, nullable=False)


class RelationLabel(db.Model):
    __tablename__ = 'relation_label'
    id = Column(Integer, primary_key=True)
    label = Column(String(255), nullable=False)
    description = Column(String(255))
    is_deleted = Column(Boolean, default=False, nullable=False)


class ActorLabel(db.Model):
    __tablename__ = 'actor_label'
    id = Column(Integer, primary_key=True)
    label = Column(String(255), nullable=False)
    description = Column(String(255))
    is_deleted = Column(Boolean, default=False, nullable=False)


class ActionLabel(db.Model):
    __tablename__ = 'action_label'
    id = Column(Integer, primary_key=True)
    label = Column(String(255), nullable=False)
    description = Column(String(255))
    is_deleted = Column(Boolean, default=False, nullable=False)


class Node(db.Model):
    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, ForeignKey('line.id'), nullable=False)
    annotator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    lexicon_id = Column(Integer, ForeignKey('lexicon.id'), nullable=False)
    label_id = Column(Integer, ForeignKey('node_label.id'), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)

    annotator = relationship('User', backref=backref('nodes', lazy='dynamic'))
    line = relationship('Line', backref=backref('nodes', lazy='dynamic'))
    lemma = relationship('Lexicon', backref=backref('nodes'))
    label = relationship('NodeLabel', backref=backref('nodes'))

    __table_args__ = (
        Index('node_line_id_annotator_id_lexicon_id_label_id',
              'line_id', 'annotator_id', 'lexicon_id', 'label_id',
              unique=True),
    )


class Relation(db.Model):
    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, ForeignKey('line.id'), nullable=False)
    annotator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    src_id = Column(Integer, ForeignKey('lexicon.id'), nullable=False)
    dst_id = Column(Integer, ForeignKey('lexicon.id'), nullable=False)
    label_id = Column(Integer, ForeignKey('relation_label.id'), nullable=False)
    detail = Column(String(255))

    is_deleted = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)

    annotator = relationship(
        'User', backref=backref('relations', lazy='dynamic')
    )
    line = relationship('Line', backref=backref('relations', lazy='dynamic'))
    src_lemma = relationship('Lexicon', foreign_keys=[src_id])
    dst_lemma = relationship('Lexicon', foreign_keys=[dst_id])
    label = relationship('RelationLabel', backref=backref('relations'))

    __table_args__ = (
        Index('relation_line_id_annotator_id_src_id_dst_id_label_id_detail',
              'line_id', 'annotator_id',
              'src_id', 'dst_id', 'label_id', 'detail', unique=True),
    )


class Action(db.Model):
    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, ForeignKey('line.id'), nullable=False)
    annotator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    label_id = Column(Integer, ForeignKey('action_label.id'), nullable=False)
    actor_label_id = Column(
        Integer, ForeignKey('actor_label.id'), nullable=False
    )
    actor_id = Column(Integer, ForeignKey('lexicon.id'), nullable=False)

    is_deleted = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)

    annotator = relationship(
        'User', backref=backref('actions', lazy='dynamic')
    )
    line = relationship('Line', backref=backref('actions', lazy='dynamic'))
    label = relationship('ActionLabel', backref=backref('actions'))
    actor_lemma = relationship('Lexicon', foreign_keys=[actor_id])
    actor_label = relationship('ActorLabel', foreign_keys=[actor_label_id])

    __table_args__ = (
        Index('action_line_id_annotator_id_actor_label_id_actor_id_label_id',
              'line_id', 'annotator_id',
              'actor_label_id', 'actor_id', 'label_id', unique=True),
    )


###############################################################################
# Setup Flask-Security

user_datastore = SQLAlchemyUserDatastore(db, User, Role)

###############################################################################


class CustomRegisterForm(RegisterForm):
    username = StringField('Username', [Required()])

    def validate(self):
        if user_datastore.find_user(username=self.username.data):
            self.username.errors = ["Username already taken"]
            return False

        if not super(CustomRegisterForm, self).validate():
            return False

        return True


class CustomLoginForm(LoginForm):
    email = StringField('Username or Email', [Required()])

###############################################################################
