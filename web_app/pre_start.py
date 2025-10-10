import logging

from werkzeug.security import generate_password_hash

from query_app.resolver import get_database
from query_app.db import User


def add_init_user(database):
    email = "admin@frances-ai.com"
    if database.get_user_by_email(email) is not None:
        # user has been registered.
        return

    # add init user to database
    # encode password
    password = "admin123"
    first_name = "Admin"
    last_name = "Admin"
    pwd_hash = generate_password_hash(password)

    try:
        user = User.create_new(first_name=first_name, last_name=last_name, password=pwd_hash, email=email)
        database.add_active_user(user)
        logging.info("user created!")
    except Exception as e:
        print(e)
        database.rollback()


database = get_database()
database.create_tables()
add_init_user(database)
