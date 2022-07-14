import os
import json
import requests

from .query_app.db import Database, DatabaseConfig
from .query_app import create_app

from defoe.config import DefoeConfig
from defoe.service import DefoeService

CONSUL_VAR_NAME = "CONSUL_ADDRESS"
CONSUL_PROTOCOL = "http://"
CONSUL_DEFAULT_ADDRESS = "localhost:8500"
CONFIG_PATH = "/v1/kv/frances/config?raw"

config = None
database = None
defoe = None

class QueryAppConfig:
  def __init__(self):
    self.defoe = None
    self.database = None

  @staticmethod
  def from_json(text):
    vals = json.loads(text)
    config = QueryAppConfig()
    config.defoe = DefoeConfig.from_dict(vals["defoe"])
    config.database = DatabaseConfig.from_dict(vals["database"])
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
  if config != None:
    return config
  url = get_config_url()
  resp = requests.get(url)
  config = QueryAppConfig.from_json(resp.text)
  return config

def get_database():
  if database != None:
    return database
  database = Database(get_config().database)
  return database

def get_defoe():
  if defoe != None:
    return defoe
  defoe = DefoeService(get_config().defoe)
  return defoe
