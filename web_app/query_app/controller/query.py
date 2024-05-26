import io

from flask import Blueprint, send_file, request, jsonify, session, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from http import HTTPStatus

from .utils import dict_defoe_queries, read_results, get_kg_type, get_kg_url

import time, os
from zipfile import *

from werkzeug.utils import secure_filename

from ..core import limiter
from flasgger import swag_from

from ..db import DefoeQueryConfig, DefoeQueryTask
from ..flask_config import DefaultFlaskConfig

query = Blueprint("query", __name__, url_prefix="/api/v1/query")
query_protected = Blueprint("query_protected", __name__, url_prefix="/api/v1/protected/query")
database = DefaultFlaskConfig.DATABASE
defoe_service = DefaultFlaskConfig.DEFOE_SERVICE
upload_folder = DefaultFlaskConfig.UPLOAD_FOLDER
result_folder = DefaultFlaskConfig.RESULTS_FOLDER
google_cloud_storage = DefaultFlaskConfig.GOOGLE_CLOUD_STORAGE


def create_defoe_query_config(kg_type, preprocess, hit_count, data_file,
                              target_sentences, target_filter, start_year, end_year,
                              window, gazetteer, bounding_box):
    config = {}
    if kg_type:
        config["kg_type"] = kg_type

    if preprocess:
        config["preprocess"] = preprocess

    if hit_count:
        config["hit_count"] = hit_count

    if data_file:
        config["data"] = data_file

    if target_sentences:
        config["target_sentences"] = target_sentences

    if target_filter:
        config["target_filter"] = target_filter

    if start_year:
        # start_year from request is integer, while defoe need string
        config["start_year"] = str(start_year)

    if end_year:
        # end_year from request is integer, while defoe need string
        config["end_year"] = str(end_year)

    if window:
        # end_year from request is integer, while defoe need string
        config["window"] = str(window)

    if gazetteer:
        config["gazetteer"] = gazetteer

    if bounding_box:
        config["bounding_box"] = bounding_box

    return config


@query_protected.route("/defoe_submit", methods=["POST"])
@swag_from("../docs/query/defoe_submit.yml")
@jwt_required()
@limiter.limit("2/minute")  # 2 requests per minute
def defoe_queries():
    user_id = get_jwt_identity()

    defoe_selection = request.json.get('defoe_selection')

    # build defoe config from request
    preprocess = request.json.get('preprocess')
    target_sentences = request.json.get('target_sentences')
    target_filter = request.json.get('target_filter')
    start_year = request.json.get('start_year')
    end_year = request.json.get('end_year')
    hit_count = request.json.get('hit_count')
    lexicon_file = request.json.get('file', '')
    data_file = os.path.join(upload_folder, user_id, lexicon_file)
    source_provider = request.json.get('source_provider', 'NLS')

    # For geoparser_by_year query, add bounding_box and gazetteer
    bounding_box = request.json.get('bounding_box')
    gazetteer = request.json.get('gazetteer')
    collection = request.json.get('collection', 'Encyclopaedia Britannica')

    kg_type = get_kg_type(collection, source_provider)

    # For terms_snippet_keysearch_by_year query, add window
    window = request.json.get('window')

    # Save config data to database
    defoe_query_config = DefoeQueryConfig.create_new(collection, source_provider, defoe_selection, preprocess, lexicon_file,
                                                     target_sentences, target_filter,
                                                     start_year, end_year, hit_count,
                                                     window, gazetteer, bounding_box)
    database.add_defoe_query_config(defoe_query_config)

    # Save defoe query task information to database

    query_task = DefoeQueryTask.create_new(user_id, defoe_query_config, "", "")
    result_filename = str(query_task.id) + ".yml"
    result_file_path = os.path.join(result_folder, user_id, str(query_task.id) + ".yml")

    if (kg_type + '_' + defoe_selection) in defoe_service.get_pre_computed_queries():
        result_file_path = defoe_service.get_pre_computed_queries()[kg_type + '_' + defoe_selection]
        result_filename = result_file_path

    query_task.resultFile = result_filename

    # create query_config for defoe query
    config = create_defoe_query_config(kg_type, preprocess, hit_count, data_file,
                                       target_sentences, target_filter, start_year, end_year, window,
                                       gazetteer, bounding_box)

    try:
        # Submit defoe query task
        defoe_service.submit_job(
            job_id=str(query_task.id),
            model_name="sparql",
            query_name=defoe_selection,
            endpoint=get_kg_url(kg_type),
            query_config=config,
            result_file_path=result_file_path
        )
        database.add_defoe_query_task(query_task)

        return jsonify({
            "success": True,
            "id": query_task.id,
        })
    except Exception as e:
        current_app.logger.info(e)
        return jsonify({
            "success": False
        })


@query_protected.route("/defoe_cancel", methods=["POST"])
@jwt_required()
def cancel_defoe_query():
    user_id = get_jwt_identity()
    task_id = request.json.get("id")
    task = database.get_defoe_query_task_by_taskID(task_id, user_id)

    if task is None:
        # No such defoe query task
        return jsonify({
            "success": False,
            "error": "No such task!"
        })

    if task.state != 'PENDING' and task.state != 'RUNNING':
        # Task has been finished, can not be cancelled
        return jsonify({
            "success": False,
            "error": "Current state: %s, Task can only be cancelled when it is pending or running!" % task.state
        })

    try:
        defoe_service.cancel_job(task_id)
        return jsonify({
            "success": True
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


@query_protected.route("/upload", methods=["POST"])
@swag_from("../docs/query/upload.yml")
@jwt_required()
@limiter.limit("2/second")  # 2 requests per second
def upload():
    user_id = get_jwt_identity()
    user_folder = os.path.join(upload_folder, user_id)
    # Make directories relative to the working folder
    os.makedirs(user_folder, exist_ok=True)
    file = request.files['file']
    submit_name = secure_filename(file.filename)
    save_name = time.strftime("%Y%m%d-%H%M%S") + "_" + submit_name
    source_file_path = os.path.join(user_folder, save_name)
    print(source_file_path)
    file.save(source_file_path)

    if current_app.config["FILE_STORAGE_MODE"] == "gs":
        # Upload it to Google Cloud Storage
        # It will look from the relative path from the working folder
        google_cloud_storage.upload_blob_from_filename(source_file_path, source_file_path)

    return jsonify({
        "success": True,
        "file": save_name,
    })


@query.route("/defoe_list", methods=["GET"])
@swag_from("../docs/query/defoe_list.yml")
def defoe_list():
    return jsonify({
        "queries": list(dict_defoe_queries().keys()),
    })


@query_protected.route("/defoe_status", methods=["POST"])
@swag_from("../docs/query/defoe_status.yml")
@jwt_required()
def defoe_status():
    user_id = get_jwt_identity()
    task_id = request.json.get("id")
    # Validate task_id
    # If the task exits
    # If the task is accessible to this user
    current_app.logger.info('defoe_status')
    current_app.logger.info('task_id: %s', task_id)

    try:
        task = database.get_defoe_query_task_by_taskID(task_id, user_id)
        # When query job is done
        if task.state == "DONE":
            return jsonify({
                "id": task_id,
                "results": task.resultFile,
                "state": task.state,
                "progress": task.progress
            })
        if task.state == "ERROR":
            return jsonify({
                "id": task_id,
                "state": "ERROR",
                "error": task.errorMsg,
                "progress": task.progress
            })

        if task.state == "CANCELLED":
            return jsonify({
                "id": task_id,
                "state": task.state,
                "progress": task.progress
            })

        # When query job is not done
        current_app.logger.info('query defoe service')
        if "precomputedResult" in task.resultFile:
            status = defoe_service.get_status(task_id, is_pre_computed=True)
        else:
            status = defoe_service.get_status(task_id)
        state = status["state"]
        output = {
            "id": task_id,
        }

        if state == "DONE":
            task.progress = 100
            output["results"] = task.resultFile

        elif state == "SETUP_DONE":
            task.progress = 5

        elif state == "RUNNING":
            task.progress = 10

        elif state == "ERROR":
            task.progress = 100
            output["error"] = status["details"]

        elif state == "CANCELLED":
            task.progress = 100

        if state != task.state:
            task.state = state
            database.update_defoe_query_task(task)

        output["state"] = task.state
        output["progress"] = task.progress

        return jsonify(output)

    except Exception as E:
        print(E)
        return jsonify({
            'error': 'Job does not exist!'
        }, HTTPStatus.BAD_REQUEST)


@query_protected.route("/defoe_query_task", methods=['POST'])
@jwt_required()
@limiter.limit("30/second")  # 30 requests per second
def defoe_query_task():
    user_id = get_jwt_identity()
    task_id = request.json.get('task_id')
    # Validate task_id
    # If this task exists
    task = database.get_defoe_query_task_by_taskID(task_id, user_id)
    if task is None:
        return jsonify({
            "error": 'This Defoe Query Task does not exist!'
        }), HTTPStatus.BAD_REQUEST
    else:
        if task.config.queryType == "frequency_keysearch_by_year":
            kg_type = get_kg_type(task.config.collection, task.config.sourceProvider)
            query_info = kg_type + "_publication_normalized"
            return jsonify({
                "task": task.to_dict(),
                "publication_normalized_result_path": defoe_service.get_pre_computed_queries()[query_info]
            }), HTTPStatus.OK
        return jsonify({
            "task": task.to_dict()
        }), HTTPStatus.OK


def result_filename_to_absolute_filepath(result_filename, user_id):
    if "precomputedResult" in result_filename:
        if current_app.config["FILE_STORAGE_MODE"] == "gs":
            return result_filename
        base_dir = str(current_app.config['BASE_DIR'])
        print(base_dir)
        print(os.path.join(base_dir, result_filename))
        return os.path.join(base_dir, result_filename)
    return os.path.join(result_folder, user_id, result_filename)


@query_protected.route("/defoe_query_result", methods=['POST'])
@jwt_required()
@limiter.limit("30/second")  # 30 requests per second
def defoe_query_result():
    user_id = get_jwt_identity()
    result_filename = request.json.get('result_filename')
    result_filepath = result_filename_to_absolute_filepath(result_filename, user_id)
    print(result_filepath)
    if current_app.config["FILE_STORAGE_MODE"] == "gs":
        # Validate file path
        # If the file exists
        # TODO If the file is accessible to this user
        # Convert result to object
        results = google_cloud_storage.read_results(result_filepath)
        return jsonify({
            "results": results
        })

    if current_app.config["FILE_STORAGE_MODE"] == "local":
        # Validate file path
        # If the file exists
        if result_filepath is not None and not os.path.isfile(result_filepath):
            print("file does not exist!")
            return jsonify({
                "error": 'File does not exist!'
            }), HTTPStatus.BAD_REQUEST
        # TODO If the file is accessible to this user
        # Convert result to object
        results = read_results(result_filepath)
        return jsonify({
            "results": results
        })


@query_protected.route("/defoe_query_tasks", methods=['POST'])
@jwt_required()
@limiter.limit("30/second")  # 30 requests per second
def defoe_query_tasks():
    user_id = get_jwt_identity()
    options = {}
    options["page"] = request.json.get("page", 1)
    options["per_page"] = request.json.get("per_page", 10)
    options["sort_by"] = request.json.get("sort_by", "submitTime")
    options["sort_order"] = request.json.get("sort_order", "desc")
    # List all defoe query tasks this user submitted
    # tasks = database.get_all_defoe_query_tasks_by_userID(user_id)
    filters = {"userID": user_id}
    tasks = database.get_defoe_query_tasks(options, filters)
    total_count = database.count_defoe_query_tasks(filters)

    return jsonify({
        "tasks": list(map(lambda task: task.to_dict(), tasks)),
        "total_count": total_count
    })


@query_protected.route("/delete_defoe_query_task", methods=['POST'])
@jwt_required()
@limiter.limit("30/second")  # 30 requests per second
def delete_defoe_query_task():
    taskID = request.json.get('taskID')
    try:
        database.delete_defoe_query_task_by_taskID(taskID)
        return jsonify({
            "deleted": True
        }), HTTPStatus.OK
    except Exception as e:
        print(e)
        database.rollback()
        return jsonify({
            "error": e
        }), HTTPStatus.BAD_REQUEST


@query_protected.route("/delete_defoe_query_tasks", methods=['POST'])
@jwt_required()
@limiter.limit("30/second")  # 30 requests per second
def delete_defoe_query_tasks():
    taskIDs = request.json.get('taskIDs')
    try:
        database.delete_defoe_query_tasks_by_taskIDs(taskIDs)
        return jsonify({
            "deleted": True
        }), HTTPStatus.OK
    except Exception as e:
        print(e)
        database.rollback()
        return jsonify({
            "error": e
        }), HTTPStatus.BAD_REQUEST


@query_protected.route("/download", methods=['POST'])
@jwt_required()
@limiter.limit("30/second")  # 30 requests per second
def download():
    user_id = get_jwt_identity()
    result_filename = request.json.get('result_filename', None)
    print(result_filename)

    result_file_path = result_filename_to_absolute_filepath(result_filename, user_id)
    print(result_file_path)
    zip_file_path = result_file_path[:-3] + "zip"

    if current_app.config["FILE_STORAGE_MODE"] == "gs":
        result_user_folder = os.path.dirname(result_file_path)
        print(result_user_folder)
        # Make directories relative to the working folder
        os.makedirs(result_user_folder, exist_ok=True)
        print(os.path.basename(result_filename))

        # It will download file to result_filename, which tells the relative path from the working folder
        google_cloud_storage.download_blob_from_filename(result_file_path, result_file_path)
        with ZipFile(zip_file_path, 'w', ZIP_DEFLATED) as zipf:
            zipf.write(result_file_path, arcname=os.path.basename(result_file_path))
    elif current_app.config["FILE_STORAGE_MODE"] == "local":
        print(zip_file_path)
        with ZipFile(zip_file_path, 'w', ZIP_DEFLATED) as zipf:
            zipf.write(result_file_path, arcname=os.path.basename(result_file_path))
    # send_file function will look for the absolute path of a file.
    return send_file(os.path.abspath(zip_file_path), as_attachment=True)
