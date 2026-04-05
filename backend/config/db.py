import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="mysql8001.site4now.net",
        user="a2df89_aiplac",
        password="kwcw@576KW",
        database="db_a2df89_aiplac"
    )