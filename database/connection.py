import psycopg2

class Connection:
    database: str
    user: str
    password: str
    host: str
    port: int
    connection: psycopg2.extensions.connection

    def __init__(self, database: str, user: str, password: str, host: str, port: int = 5432):
        self.database = database
        self.user = user
        self.password = password
        self.host = host
        self.port = port

        self.connect()
        self.init_database()

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                database=self.database,
                user=self.user,
                password=self.password,
                host=self.host,
                port=self.port
            )
            print("Connected to database")
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")

    def init_database(self):
        with open("database/schema.sql", "r") as file:
            schema = file.read()

        cursor = self.connection.cursor()
        cursor.execute(schema)
        self.connection.commit()
        cursor.close()

    def close(self):
        self.connection.close()
        print("Connection closed")

    def insert_user(self, user_id: str, timezone: str):
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO user_timezone (user_id, timezone) VALUES (%s, %s)", (user_id, timezone))
        self.connection.commit()
        cursor.close()

    def get_user(self, user_id: int):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM user_timezone WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return user
    
    def delete_user(self, user_id: int):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM user_timezone WHERE user_id = %s", (user_id,))
        self.connection.commit()
        cursor.close()

    def insert_message(self, message_id: int, timestamp: int):
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO message_id_timestamp (message_id, timestamp) VALUES (%s, %s)", (message_id, timestamp))
        self.connection.commit()
        cursor.close()

    def get_message(self, message_id: int):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM message_id_timestamp WHERE message_id = %s", (message_id,))
        message = cursor.fetchone()
        cursor.close()
        return message
    
    def delete_message(self, message_id: int):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM message_id_timestamp WHERE message_id = %s", (message_id,))
        self.connection.commit()
        cursor.close()