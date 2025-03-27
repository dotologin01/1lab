import os

SECRET_KEY = 'secret-key'

SQLALCHEMY_DATABASE_URI = 'sqlite:///project.db'
# SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:16745678@127.0.0.1/user_management'

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'images')
