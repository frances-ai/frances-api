import os
import json
import requests

from .db import Database, DatabaseConfig

from defoe_lib.config import DefoeConfig
from defoe_lib.service import DefoeService

from .controller.models import ModelsRepository
from .controller.files import FilesConfig

CONSUL_VAR_NAME = "CONSUL_ADDRESS"
CONSUL_PROTOCOL = "http://"
CONSUL_DEFAULT_ADDRESS = "localhost:8500"
CONFIG_PATH = "/v1/kv/frances/config?raw"

config = None
frances = None
defoe = None
models = None
database = None


class QueryAppConfig:
  def __init__(self):
    self.defoe = None
    self.database = None
    self.files = None

  @staticmethod
  def from_json(text):
    vals = json.loads(text)
    config = QueryAppConfig()
    config.frances = FrancesConfig.from_dict(vals["frances"])
    config.defoe = DefoeConfig.from_dict(vals["defoe"])
    config.database = DatabaseConfig.from_dict(vals["database"])
    return config

class FrancesConfig:
  def __init__(self, fuseki_url="", files=None):
    self.fuseki_url = fuseki_url
    self.files = files
  
  @staticmethod
  def from_dict(vals):
    config = FrancesConfig()
    config.fuseki_url = vals["fusekiUrl"]
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
  print("Resolved consul address as: " + url)
  
  resp = requests.get(url)
  print("Consul config retrieved:")
  print(resp.text)
  
  config = QueryAppConfig.from_json(resp.text)
  return config

def get_frances():
  # this is only a config
  return get_config().frances

def get_files():
  # this is only a config
  return get_frances().files

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
  models = ModelsRepository(get_files())
  return models

def get_database():
  global database
  if database != None:
    return database
  database = Database(get_config().database)
  return database

