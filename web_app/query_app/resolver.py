import os
import json
import requests

from .db import Database, DatabaseConfig

from defoe_lib.config import DefoeConfig
from defoe_lib.service import DefoeService

from .controller.models import ModelsConfig, ModelsRepository
from .controller.files import FilesConfig

CONSUL_VAR_NAME = "CONSUL_ADDRESS"
CONSUL_PROTOCOL = "http://"
CONSUL_DEFAULT_ADDRESS = "localhost:8500"
CONFIG_PATH = "/v1/kv/frances/config?raw"

config = None
defoe = None
models = None
database = None


class QueryAppConfig:
  def __init__(self):
    self.defoe = None
    self.models = None
    self.database = None
    self.files = None

  @staticmethod
  def from_json(text):
    vals = json.loads(text)
    config = QueryAppConfig()
    config.defoe = DefoeConfig.from_dict(vals["defoe"])
    config.models = ModelsConfig.from_dict(vals["models"])
    config.database = DatabaseConfig.from_dict(vals["database"])
    config.files = FilesConfig.from_dict(vals["files"])
    return config


def get_config_url():
  consul_var = os.getenv(CONSUL_VAR_NAME)
  consul_address = None
  
  if consul_var != None:
    consul_address = consul_var
  else:
    consul_address = CONSUL_DEFAULT_ADDRESS
  
  return CONSUL_PROTOCOL + consul_address + CONFIG_PATH

def get_config():
  global config
  if config != None:
    return config
  url = get_config_url()
  resp = requests.get(url)
  config = QueryAppConfig.from_json(resp.text)
  return config

def get_defoe():
  global defoe
  if defoe != None:
    return defoe
  defoe = DefoeService(get_config().defoe)
  return defoe

def get_models():
  global models
  if models != None:
    return models
  models = ModelsRepository(get_config().models)
  return models

def get_database():
  global database
  if database != None:
    return database
  database = Database(get_config().database)
  return database

def get_files():
  # this is only a config
  return get_config().files
