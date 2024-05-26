"""
Run Spark text query job.

    usage: run_query.py [-r [RESULTS_FILE]]
                       [-r [RESULTS_FILE]]
                       model_name query_name [query_config_file]

    Run Spark text analysis job

    positional arguments:
      sparql_endpoint       endpoint to query data
      model_name            Data model to which data files conform:
      ['books', 'papers', 'fmp','nzpp', 'generic_xml', 'nls', 'hdfs', 'psql', 'es', 'nlsArticles']
      query_name            Query module name

    optional arguments:
      -h, --help            show this help message and exit
      -n [NUM_CORES], --num_cores [NUM_CORES]
                            Number of cores
      -r [RESULTS_FILE], --results_file [RESULTS_FILE]
                            Query results file
      -e [ERRORS_FILE], --errors_file [ERRORS_FILE]
                            Errors file
      query_config_file     Query-specific configuration file

* data_file: lists either URLs or paths to files on the file system.
* model_name: text model to be used. The model determines the modules
  loaded. Given a "model_name" value of "<MODEL_NAME>" then a module
  "defoe.<MODEL_NAME>.setup" must exist and support a function:

    tuple(Object | str or unicode, str or unicode)
    filename_to_object(str or unicode: filename)

  - tuple(Object, None) is returned where Object is an instance of the
  - object model representing the data, if the file was successfully
  - read and parsed into an object
  - tuple(str or unicode, filename) is returned with the filename and
  - an error message, if the file was not successfully read and parsed
  - into an object
* query_name: name of Python module implementing the query to run
  e.g. "defoe.alto.queries.find_words_group_by_word" or
  "defoe.papers.queries.articles_containing_words". The query must be
  compatible with the chosen model in "model_name". The module
  must support a function

    list do_query(pyspark.rdd.PipelinedRDD rdd,
                  str|unicode config_file,
                  py4j.java_gateway.JavaObject logger)

* "query_config_file": query-specific configuration file. This is
  optional and depends on the chosen query module above.
* results_file": name of file to hold query results in YAML
  format. Default: "results.yml".
"""
import argparse
import yaml
from google.cloud import storage
from pyspark.sql import SparkSession

from defoe import sparql
from defoe.spark_utils import files_to_rdd


def create_arg_parser():  # pragma: no cover
    parser = argparse.ArgumentParser(
        description='Submit a defoe query')
    parser.add_argument('--query_name', help='name of defoe query', required=True)
    parser.add_argument('--model_name', help='name of data model', required=True)
    parser.add_argument('--endpoint', help='endpoint of dataset')
    parser.add_argument('--kg_type', help='type of knowledge graph', default=None)
    parser.add_argument('--preprocess', help='preprocess name', default=None)
    parser.add_argument('--target_sentences', help='target_sentences', default=None)
    parser.add_argument('--target_filter', help='target_sentences', default=None)
    parser.add_argument('--start_year', help='target_sentences', default=None)
    parser.add_argument('--end_year', help='target_sentences', default=None)
    parser.add_argument('--hit_count', help='target_sentences', default=None)
    parser.add_argument('--window', help='target_sentences', default=None)
    parser.add_argument('--gazetteer', help='gazetteer', default=None)
    parser.add_argument('--bounding_box', help='bounding_box', default=None)
    parser.add_argument('--data', metavar='input file', default=None,
                        help='file containing input dataset in TXT')
    parser.add_argument('--result_file_path', metavar='result_file',
                        help='result_file stored in google cloud storage', required=True)
    return parser


def parse_common_args():  # pragma: no cover
    parser = create_arg_parser()
    return parser.parse_known_args()


def load_inputs(args, bucket):
    query_name = args.query_name
    model_name = args.model_name
    endpoint = args.endpoint
    result_file_path = args.result_file_path
    query_config = {}
    if args.kg_type is not None:
        query_config['kg_type'] = args.kg_type

    if args.data is not None:
        query_config['data'] = bucket.blob(args.data)

    if args.preprocess is not None:
        query_config['preprocess'] = args.preprocess

    if args.target_sentences is not None:
        query_config['target_sentences'] = args.target_sentences.split(",")

    if args.target_filter is not None:
        query_config['target_filter'] = args.target_filter

    if args.start_year is not None:
        query_config['start_year'] = args.start_year

    if args.end_year is not None:
        query_config['end_year'] = args.end_year

    if args.hit_count is not None:
        query_config['hit_count'] = args.hit_count

    if args.window is not None:
        query_config['window'] = args.window

    if args.gazetteer is not None:
        query_config['gazetteer'] = args.gazetteer

    if args.bounding_box is not None:
        query_config['bounding_box'] = args.bounding_box

    return query_config, query_name, model_name, endpoint, result_file_path


models = {
    "sparql": sparql.Model(),
}


def main():
    """
    Run Spark text analysis job.
    """

    PROJECT_ID = "frances-365422"
    BUCKET_NAME = "frances2023"
    bucket = storage.Client(PROJECT_ID).bucket(BUCKET_NAME)

    args, remaining = parse_common_args()
    query_config, query_name, model_name, endpoint, result_file_path = load_inputs(args, bucket)

    print(model_name)
    if model_name not in models:
        raise Exception("'model_name' must be one of " + str(models))

    model = models[model_name]

    if query_name not in model.get_queries():
        raise Exception("'query_name' must be one of " + str(model.get_queries()))

    query = model.get_queries()[query_name]

    # Submit job.
    spark = SparkSession.builder.appName("defoe").getOrCreate()
    log = spark._jvm.org.apache.log4j.LogManager.getLogger(__name__)  # pylint: disable=protected-access

    ok_data = model.endpoint_to_object(endpoint, spark)

    results = query(ok_data, query_config, log, spark)
    result_file = bucket.blob(result_file_path)

    if results is not None:
        with result_file.open('w') as f:
            f.write(yaml.safe_dump(dict(results)))


if __name__ == "__main__":
    main()
