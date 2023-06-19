import psycopg2
from config import *


class Conn:
    def __init__(self):
        self.connection = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )
        self.connection.autocommit = True

    def get_data(self, query, mode):
        with self.connection.cursor() as cursor:
            cursor.execute(query)
            if mode == 1:
                re = cursor.fetchone()
            if mode == 2:
                re = cursor.fetchall()
            if mode != 0:
                return re


connect = Conn()
