#penggunaan konsep OOP untuk mengelola koneksi database dan operasi terkait pengguna pada tabel "users" menggunakan SQLite di Python.
import sqlite3

class DatabaseDoorlock:
    #membuka koneksi ke database dan membuat objek cursor untuk menjalankan perintah SQL.
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    #execute_query untuk menjalankan perintah SQL pada database.jika terdapat parameter, parameter akan dimasukkan ke dalam perintah SQL.
    def execute_query(self, query, params=None):
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        self.conn.commit()

    #fetch_data untuk mengeksekusi perintah SQL dan mengembalikan hasilnya. jika terdapat parameter, parameter akan dimasukkan ke dalam perintah SQL.
    def fetch_data(self, query, params=None):
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        return self.cursor.fetchall()

    #menutup koneksi ke database
    def close_connection(self):
        self.conn.close()

class User:
    def __init__(self, doorlock):
        self.doorlock = doorlock
    
    #membuat tabel users.
    def create_table(self):
        query = '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR NOT NULL,
            username VARCHAR NOT NULL,
            password VARCHAR NOT NULL
        )
        '''
        self.doorlock.execute_query(query)

    #menambahkan data user baru ke dalam tabel "users".
    def insert_user(self, email, username, password):
        query = "INSERT INTO users (email, username, password) VALUES (?, ?, ?)"
        params = (email, username, password)
        self.doorlock.execute_query(query, params)

    #mengambil semua data user dari tabel "users".
    def get_all_users(self):
        query = 'SELECT * FROM users'
        return self.doorlock.fetch_data(query)

#membuat objek DatabaseDoorlock.
doorlock = DatabaseDoorlock("mydatabase.db")

#membuat objek User.
user = User(doorlock)

#membuat tabel users (jika belum ada).
user.create_table()

#menambahkan user ke dalam database.
user.insert_user("myemail@gmai.com", "myusername", "mypassword")

#mengambil semua data user dari database.
all_users = user.get_all_users()
print("all_users:")
for user in all_users:
    print(user)

#menutup koneksi database.
doorlock.close_connection()
