import psycopg2
import psycopg2.extras

import time
import uuid
from pathlib import Path

# Find path to web-app, which is the base directory.
base_path = Path(__file__).parent.parent
# Find path for sql script file for tables creation.
tables_file_path = base_path.joinpath("db/tables.sql")

namespace = "github.com/frances-ai/frances-api"

psycopg2.extras.register_uuid()


class DatabaseConfig:
    def __init__(self):
        self.host = ""
        self.user = ""
        self.password = ""

    @staticmethod
    def from_dict(vals):
        config = DatabaseConfig()
        config.host = vals["host"]
        config.user = vals["user"]
        config.password = vals["password"]
        return config


def record_to_defoe_query_task(record):
    config_record = record[:13]
    task_record = record[13:]
    return DefoeQueryTask(*task_record[0:2], DefoeQueryConfig(*config_record), *task_record[3:])


class Database:
    def __init__(self, config):
        self.db = psycopg2.connect(
            host=config["host"],
            port="5432",
            user=config["user"],
            password=config["password"]
        )
        self.create_tables()

    def rollback(self):
        self.db.rollback()

    def create_tables(self):
        f = open(tables_file_path, "r")
        queries = f.read()
        self.db.cursor().execute(queries)
        self.db.commit()

    def get_pending_users(self):
        sql = "SELECT userId, firstName, lastName,email,password FROM Users WHERE status='pending';"
        cursor = self.db.cursor()
        cursor.execute(sql)

        results = cursor.fetchall()
        if len(results) == 0:
            return None
        res = results[0]
        users = []
        for res in results:
            users.append(User(*res))
        return users

    def get_active_users(self):
        sql = "SELECT userId, firstName, lastName,email,password FROM Users WHERE status='active';"
        cursor = self.db.cursor()
        cursor.execute(sql)

        results = cursor.fetchall()
        if len(results) == 0:
            return None
        res = results[0]
        users = []
        for res in results:
            users.append(User(*res))
        return users

    def activateUser(self, id):
        print("User ID is:",id)
     
        sql = "UPDATE users SET status='active' WHERE UserID=%s and status='pending';"
        cursor = self.db.cursor()
        cursor.execute(sql, (id,))
        self.db.commit()
        return

    def deleteUser(self, id):
        print("User ID is:",id)
     
        sql = "UPDATE users SET status='deleted' WHERE UserID=%s;"
        
        cursor = self.db.cursor()
        cursor.execute(sql, (id,))
        self.db.commit()
        return


    def get_active_user_by_id(self, id):
        sql = "SELECT userId, firstName, lastName,email,password FROM Users WHERE UserID=%s and status='active';"
        cursor = self.db.cursor()
        cursor.execute(sql, (id,))

        results = cursor.fetchall()
        if len(results) == 0:
            return None

        res = results[0]
        return User(*res)

    def get_active_user_by_email(self, email):
        sql = "SELECT userId,firstName, lastName,email,password FROM Users WHERE email=%s and status='active';"
        cursor = self.db.cursor()
        cursor.execute(sql, (email,))

        results = cursor.fetchall()
        if len(results) == 0:
            return None

        res = results[0]
        return User(*res)

    def get_user_by_email(self, email):
        sql = "SELECT userId,firstName, lastName,email,password FROM Users WHERE email=%s;"
        cursor = self.db.cursor()
        cursor.execute(sql, (email,))

        results = cursor.fetchall()
        if len(results) == 0:
            return None

        res = results[0]
        return User(*res)

    def add_user(self, user):
        sql = "INSERT INTO Users (userId, firstName, lastName, email, password) VALUES (%s, %s, %s, %s, %s);"
        vals = (user.id, user.first_name, user.last_name, user.email, user.password)

        cursor = self.db.cursor()
        cursor.execute(sql, vals)
        self.db.commit()
        return

    def add_defoe_query_task(self, task):
        sql = "INSERT INTO DefoeQueryTasks (taskID, userID, configID, resultFile, progress, state, errorMsg) VALUES (%s, %s, %s, %s, %s, %s, %s);"
        vals = (task.id, task.user_id, task.config.id, task.resultFile, task.progress, task.state, task.errorMsg)

        cursor = self.db.cursor()
        cursor.execute(sql, vals)
        self.db.commit()
        return

    def update_defoe_query_task(self, task):
        sql = "UPDATE DefoeQueryTasks SET progress=%s, state=%s, errorMsg=%s WHERE taskID=%s;"
        vals = (task.progress, task.state, task.errorMsg, task.id)

        cursor = self.db.cursor()
        cursor.execute(sql, vals)
        self.db.commit()
        return

    def get_defoe_query_task_by_taskID(self, taskID, userID):
        sql = "SELECT * " \
              "FROM DefoeQueryConfigs " \
              "INNER JOIN DefoeQueryTasks ON DefoeQueryTasks.configID = DefoeQueryConfigs.configID " \
              "WHERE DefoeQueryTasks.taskID=%s " \
              "AND DefoeQueryTasks.userID=%s;"
        cursor = self.db.cursor()
        cursor.execute(sql, (taskID, userID))

        records = cursor.fetchall()
        if len(records) == 0:
            return None

        record = records[0]
        return record_to_defoe_query_task(record)

    def get_all_defoe_query_tasks_by_userID(self, userID):
        sql = "SELECT * " \
              "FROM  DefoeQueryConfigs " \
              "INNER JOIN DefoeQueryTasks ON DefoeQueryTasks.configID = DefoeQueryConfigs.configID " \
              "WHERE DefoeQueryTasks.userID=%s;"
        cursor = self.db.cursor()
        cursor.execute(sql, (userID,))

        records = cursor.fetchall()
        if len(records) == 0:
            return None
        results = []
        for record in records:
            results.append(record_to_defoe_query_task(record))

        return results

    def add_defoe_query_config(self, config):
        sql = "INSERT INTO  DefoeQueryConfigs(configID, collection, queryType, preprocess, lexiconFile, targetSentences, targetFilter, startYear, endYear, hitCount, snippetWindow, gazetteer, boundingBox)" \
              " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        vals = (
            config.id, config.collection, config.queryType, config.preprocess, config.lexiconFile,
            config.targetSentences,
            config.targetFilter, config.startYear, config.endYear, config.hitCount, config.window, config.gazetteer,
            config.boundingBox)

        cursor = self.db.cursor()
        cursor.execute(sql, vals)
        self.db.commit()
        return

    def get_defoe_query_config_by_id(self, id):
        sql = "SELECT * FROM DefoeQueryConfigs WHERE configID=%s;"
        cursor = self.db.cursor()
        cursor.execute(sql, (id,))

        records = cursor.fetchall()
        if len(records) == 0:
            return None

        record = records[0]
        return DefoeQueryConfig(*record)


class User:
    def __init__(self, id, first_name, last_name, email, password):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password

    @staticmethod
    def create_new(first_name, last_name, email, password):
        id = uuid.uuid5(uuid.NAMESPACE_URL, namespace + first_name + str(time.time()))
        return User(id, first_name, last_name, email, password)

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "password": self.password
        }


class DefoeQueryConfig:
    def __init__(self, id, collection, queryType, preprocess, lexiconFile, targetSentences, targetFilter, startYear,
                 endYear,
                 hitCount, window, gazetteer, boundingBox):
        self.id = id
        self.collection = collection
        self.preprocess = preprocess
        self.queryType = queryType
        self.lexiconFile = lexiconFile
        self.targetSentences = targetSentences
        self.targetFilter = targetFilter
        self.startYear = startYear
        self.endYear = endYear
        self.hitCount = hitCount
        self.window = window
        self.gazetteer = gazetteer
        self.boundingBox = boundingBox

    @staticmethod
    def create_new(collection, queryType, preprocess, lexiconFile, targetSentences, targetFilter, startYear, endYear,
                   hitCount, window, gazetteer, boundingBox):
        id = uuid.uuid5(uuid.NAMESPACE_URL, namespace + lexiconFile + str(time.time()))
        return DefoeQueryConfig(id, collection, queryType, preprocess, lexiconFile, targetSentences, targetFilter,
                                startYear, endYear, hitCount,
                                window, gazetteer, boundingBox)

    def to_dict(self):
        return {
            "collection": self.collection,
            "queryType": self.queryType,
            "preprocess": self.preprocess,
            "lexiconFile": self.lexiconFile,
            "targetSentences": self.targetSentences,
            "targetFilter": self.targetFilter,
            "startYear": self.startYear,
            "endYear": self.endYear,
            "hitCount": self.hitCount,
            "window": self.window,
            "gazetteer": self.gazetteer,
            "boundingBox": self.boundingBox
        }


class DefoeQueryTask:
    def __init__(self, id, user_id, config, resultFile, progress, state, errorMsg, submitTime):
        self.id = id
        self.user_id = user_id
        self.config = config
        self.resultFile = resultFile
        self.progress = progress
        self.state = state
        self.errorMsg = errorMsg
        self.submitTime = submitTime

    @staticmethod
    def create_new(user_id, config, resultFile, errorMsg):
        id = uuid.uuid5(uuid.NAMESPACE_URL, namespace + resultFile + str(time.time()))
        return DefoeQueryTask(id, user_id, config, resultFile, 0, "PENDING", errorMsg, "")

    def to_dict(self):
        return {
            "task_id": self.id,
            "config": self.config.to_dict(),
            "resultFile": self.resultFile,
            "progress": self.progress,
            "state": self.state,
            "errorMsg": self.errorMsg,
            "submit_time": self.submitTime.strftime("%Y-%m-%d %H:%M:%S.%f")
        }


if __name__ == "__main__":
    config = DatabaseConfig()
    config.host = "127.0.0.1"
    config.user = "frances"
    config.password = "frances"

    db = Database(config)

    user = User.create_new("wilfrid", "kins", "in@gmail.com", "abcabc")
    db.add_user(user)

    u = db.get_active_user_by_id(user.id)
    print("user")
    print(u.first_name)
    print(u.email)
    print()

    u = db.get_user_by_email('damonyu97@hotmail.com')
    print(u)

    # Mock Defoe Query Task Submit

    # Save config
    config = DefoeQueryConfig.create_new("eb", "public", "None", "lexiconpath", "", "any", 1771, 1771, "word", 10);
    db.add_defoe_query_config(config)

    # Save Task
    task = DefoeQueryTask.create_new(user.id, config.id, "", 0, "")
    db.add_defoe_query_task(task)

    taskInfo = db.get_defoe_query_task_by_taskID(task.id)
    print(taskInfo.submitTime)
    print(taskInfo.progress)

    taskInfo.progress = 2
    db.update_defoe_query_task(taskInfo)

    updatedTask = db.get_defoe_query_task_by_taskID(taskInfo.id)
    print(updatedTask.progress)
