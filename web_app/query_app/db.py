import psycopg2
import psycopg2.extras

import time
import uuid
from pathlib import Path

# Find path to web-app, which is the base directory.
base_path = Path(__file__).parent.parent
# Find path for sql script file for tables creation.
tables_file_path = base_path.joinpath("db/tables.sql")
db_update_file_path = base_path.joinpath("db/updates.sql")

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
    print(record)
    config_record = record[:16]
    task_record = record[16:]
    return DefoeQueryTask(*task_record[0:2], DefoeQueryConfig(*config_record), *task_record[3:])


class Database:
    def __init__(self, config):
        print(config["host"])
        self.db = psycopg2.connect(
            host=config["host"],
            port="5432",
            user=config["user"],
            password=config["password"]
        )
        self.create_tables()
        #self.update_database()

    def rollback(self):
        self.db.rollback()

    def create_tables(self):
        f = open(tables_file_path, "r")
        queries = f.read()
        self.db.cursor().execute(queries)
        self.db.commit()

    def update_database(self):
        f = open(db_update_file_path, "r")
        queries = f.read()
        self.db.cursor().execute(queries)
        self.db.commit()

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

    def add_active_user(self, user):
        sql = "INSERT INTO Users (userId, firstName, lastName, email, password, status) VALUES (%s, %s, %s, %s, %s, 'active');"
        vals = (user.id, user.first_name, user.last_name, user.email, user.password)

        cursor = self.db.cursor()
        cursor.execute(sql, vals)
        self.db.commit()
        return

    def add_visit(self, visit):
        sql = "INSERT INTO StatsVisits (visitId, ip, page) VALUES (%s, %s, %s);"
        vals = (visit.id, visit.ip, visit.page)

        cursor = self.db.cursor()
        cursor.execute(sql, vals)
        self.db.commit()
        return

    def get_number_of_visits(self):
        sql = "SELECT COUNT(*) FROM StatsVisits;"
        cursor = self.db.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        if len(results) == 0:
            return None
        res = results[0]
        return res

    def add_defoe_query_task(self, task):
        sql = "INSERT INTO DefoeQueryTasks (taskID, userID, configID, resultFile, progress, state, errorMsg) VALUES (%s, %s, %s, %s, %s, %s, %s);"
        vals = (task.id, task.user_id, task.config.id, task.resultFile, task.progress, task.state, task.errorMsg)

        cursor = self.db.cursor()
        cursor.execute(sql, vals)
        self.db.commit()
        return

    def delete_defoe_query_tasks_by_taskIDs(self, taskIDs):
        placeholders = ', '.join(['%s'] * len(taskIDs))
        sql = f"DELETE FROM DefoeQueryTasks WHERE taskID IN ({placeholders});"
        cursor = self.db.cursor()
        cursor.execute(sql, taskIDs)
        self.db.commit()
        return

    def delete_defoe_query_task_by_taskID(self, taskID):
        sql = "DELETE FROM DefoeQueryTasks WHERE taskID=%s;"
        cursor = self.db.cursor()
        cursor.execute(sql, (taskID))
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

    def count_defoe_query_tasks(self, filters):

        sql = "SELECT COUNT(*) " \
              "FROM  DefoeQueryConfigs " \
              "INNER JOIN DefoeQueryTasks ON DefoeQueryTasks.configID = DefoeQueryConfigs.configID "
        first_condition = True
        for condition in filters:
            if condition:
                if first_condition:
                    sql += " WHERE " + condition + "=%s"
                    first_condition = False
                else:
                    sql += " AND " + condition + "=%s"

        sql += ";"
        cursor = self.db.cursor()
        cursor.execute(sql, tuple(value for key, value in filters.items()))

        tasks_count = cursor.fetchone()[0]
        return tasks_count

    def get_defoe_query_tasks(self, options, filters):
        page = options["page"]
        per_page = options["per_page"]
        # Calculate offset
        offset = (page - 1) * per_page
        sort_by = options["sort_by"]
        sort_order = options["sort_order"]

        sql = "SELECT * " \
              "FROM  DefoeQueryConfigs " \
              "INNER JOIN DefoeQueryTasks ON DefoeQueryTasks.configID = DefoeQueryConfigs.configID "

        first_condition = True
        for condition in filters:
            if condition:
                if first_condition:
                    sql += " WHERE " + condition + "=%s"
                    first_condition = False
                else:
                    sql += " AND " + condition + "=%s"

        sql += f" ORDER BY {sort_by} {sort_order} " \
               f" LIMIT {per_page} OFFSET {offset};"
        cursor = self.db.cursor()
        cursor.execute(sql, tuple(value for key, value in filters.items()))

        records = cursor.fetchall()
        results = []
        for record in records:
            results.append(record_to_defoe_query_task(record))

        return results

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
        sql = "INSERT INTO  DefoeQueryConfigs(configID, collection, queryType, preprocess, lexiconFile, " \
              "targetSentences, targetFilter, startYear, endYear, hitCount, snippetWindow, gazetteer, " \
              "boundingBox, sourceProvider, level, excludeWords)" \
              " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"
        vals = (
            config.id, config.collection, config.queryType, config.preprocess,
            config.lexiconFile,
            config.targetSentences,
            config.targetFilter, config.startYear, config.endYear, config.hitCount, config.window, config.gazetteer,
            config.boundingBox, config.sourceProvider, config.level, config.excludeWords)

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


class Visit:
    def __init__(self, id, ip, page):
        self.id = id
        self.ip = ip
        self.page = page

    @staticmethod
    def create_new(ip, page):
        id = uuid.uuid5(uuid.NAMESPACE_URL, namespace + ip + str(time.time()))
        return Visit(id, ip, page)


class DefoeQueryConfig:
    def __init__(self, id, collection, queryType, preprocess, lexiconFile, targetSentences,
                 targetFilter, startYear,
                 endYear,
                 hitCount, window, gazetteer, boundingBox, sourceProvider, level, excludeWords):
        self.id = id
        self.collection = collection
        self.sourceProvider = sourceProvider
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
        self.level = level
        self.excludeWords = excludeWords

    @staticmethod
    def create_new(collection, sourceProvider, queryType, preprocess, lexiconFile, targetSentences, targetFilter,
                   startYear, endYear,
                   hitCount, window, gazetteer, boundingBox, level, excludeWords):
        id = uuid.uuid5(uuid.NAMESPACE_URL, namespace + lexiconFile + str(time.time()))
        return DefoeQueryConfig(id, collection, queryType, preprocess, lexiconFile, targetSentences,
                                targetFilter,
                                startYear, endYear, hitCount,
                                window, gazetteer, boundingBox, sourceProvider, level, excludeWords)

    def to_dict(self):
        return {
            "collection": self.collection,
            "sourceProvider": self.sourceProvider,
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
            "boundingBox": self.boundingBox,
            "level": self.level,
            "excludeWords": self.excludeWords
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
