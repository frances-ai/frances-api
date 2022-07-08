import psycopg2
import psycopg2.extras

import time
import uuid

tables_file_path = "./db/tables.sql"
namespace = "github.com/frances-ai/frances-api"

psycopg2.extras.register_uuid()


class DatabaseConfig:
    def __init__(self):
        self.host = ""
        self.user = ""
        self.password = ""
        self.database = ""


class Database:
    def __init__(self, config):
        self.db = psycopg2.connect(
            host=config.host,
            port="5432",
            user=config.user,
            password=config.password
        )
        self.create_tables()

    def create_tables(self):
        f = open(tables_file_path, "r")
        queries = f.read()
        self.db.cursor().execute(queries)
        self.db.commit()

    def get_user_by_id(self, id):
        sql = "SELECT UserId,FullName,Email,Password FROM Users WHERE UserID=%s;"
        cursor = self.db.cursor()
        cursor.execute(sql, (id,))

        results = cursor.fetchall()
        if len(results) == 0:
            return None

        res = results[0]
        return User(*res)

    def get_user_by_email(self, email):
        sql = "SELECT UserId,FullName,Email,Password FROM Users WHERE Email=%s;"
        cursor = self.db.cursor()
        cursor.execute(sql, (email,))

        results = cursor.fetchall()
        if len(results) == 0:
            return None

        res = results[0]
        return User(*res)

    def add_user(self, user):
        sql = "INSERT INTO Users (UserId, FullName, Email, Password) VALUES (%s, %s, %s, %s);"
        vals = (user.id, user.name, user.email, user.password)

        cursor = self.db.cursor()
        cursor.execute(sql, vals)
        self.db.commit()
        return

    def add_submission(self, sub):
        sql = "INSERT INTO Submissions (submissionID, userID, FullName, result, error) VALUES (%s, %s, %s, %s, %s);"
        vals = (sub.id, sub.userID, sub.name, sub.result, sub.error)

        cursor = self.db.cursor()
        cursor.execute(sql, vals)
        self.db.commit()
        return

    def update_submission(self, sub):
        sql = "UPDATE Submissions SET userID=%s, fullName=%s, result=%s, error=%s WHERE submissionID=%s;"
        vals = (sub.userID, sub.name, sub.result, sub.error, sub.id)

        cursor = self.db.cursor()
        cursor.execute(sql, vals)
        self.db.commit()
        return

    def get_submissions(self, userID):
        sql = "SELECT submissionID, userID, fullName, result, error, submitTime FROM Submissions WHERE userID=%s;"
        cursor = self.db.cursor()
        cursor.execute(sql, (userID,))

        records = cursor.fetchall()
        subs = []
        for row in records:
            subs.append(Submission(*row))
        return subs


# Initialise database
DATABASE_CONFIG = DatabaseConfig()
DATABASE_CONFIG.host = "127.0.0.1"
DATABASE_CONFIG.user = "frances"
DATABASE_CONFIG.password = "frances"
db = Database(DATABASE_CONFIG)


class User:
    def __init__(self, id, name, email, password):
        self.id = id
        self.name = name
        self.email = email
        self.password = password

    @staticmethod
    def create_new(name, email, password):
        id = uuid.uuid5(uuid.NAMESPACE_URL, namespace + name + str(time.time()))
        return User(id, name, email, password)


class Submission:
    def __init__(self, id, userID, name, result, error, time):
        self.id = id
        self.userID = userID
        self.name = name
        self.result = result
        self.error = error
        self.time = time

    @staticmethod
    def create_new(userID, name, result, error):
        id = uuid.uuid5(uuid.NAMESPACE_URL, namespace + name + str(time.time()))
        return Submission(id, userID, name, result, error, "")


if __name__ == "__main__":
    config = DatabaseConfig()
    config.host = "127.0.0.1"
    config.user = "frances"
    config.password = "frances"

    db = Database(config)

    user = User.create_new("wilfrid-askins", "wilfridaskins@gmail.com", "abcabc")
    db.add_user(user)

    u = db.get_user_by_id(user.id)
    print("user")
    print(u.name)
    print(u.email)
    print()

    u = db.get_user_by_email('damonyu97@hotmail.com')
    print(u)

    sub = Submission.create_new(user.id, "basic-job-1", "result1234", "")
    db.add_submission(sub)

    sub1 = Submission.create_new(user.id, "basic-job-2", "", "")
    db.add_submission(sub1)

    for sub in db.get_submissions(user.id):
        print("submission")
        print(sub.id)
        print(sub.result)
        print(sub.error)

    sub1.result = "blahblah"
    sub1.error = "error job failed"
    db.update_submission(sub1)

    for sub in db.get_submissions(user.id):
        print("submission")
        print(sub.id)
        print(sub.result)
        print(sub.error)
