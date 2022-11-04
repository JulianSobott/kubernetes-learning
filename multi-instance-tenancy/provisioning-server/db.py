import logging
import os

import mariadb

from models import InstanceConfig, Database

db_password = os.environ.get("DB_PASSWORD", "default")
db_host = os.environ.get("DB_HOST")


def create_database(conf: InstanceConfig):
    with mariadb.connect(
            user="root",
            password=os.environ.get("DB_PASSWORD", "default"),
            host=db_host,
            port=3306,
    ) as conn:
        try:
            with conn.cursor() as cursor:
                # we can use f-strings here because we're not using user input
                # all data is coming from internal sources
                cursor.execute(f"CREATE DATABASE {conf.db.database};")
                cursor.execute(
                    f"CREATE USER {conf.db.user} IDENTIFIED BY '{conf.db.password}';"
                )
                cursor.execute(
                    f"GRANT ALL PRIVILEGES ON {conf.db.database}.* TO {conf.db.user};"
                )
                cursor.execute("FLUSH PRIVILEGES;")

        except Exception as e:
            return e


def delete_database(database: str, user: str):
    with mariadb.connect(
        host=db_host,
        user="root",
        password=db_password,
    ) as connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"DROP DATABASE {database};")
                cursor.execute(f"DROP USER {user};")
                cursor.execute("FLUSH PRIVILEGES;")
        except Exception as e:
            return e


if __name__ == '__main__':
    res = create_database(InstanceConfig(
        name="test",
        slug="test",
        tenant_id="test",
        db=Database(
            user="test_user",
            password="password",
            host=db_host,
            database="test",
        ),
    ))
    print(res)
