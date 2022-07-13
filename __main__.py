import os
import json
import requests

from .web_app.query_app.db import DatabaseConfig
from defoe.config import DefoeConfig

CONSUL_VAR_NAME = "CONSUL_ADDRESS"
CONSUL_PROTOCOL = "http://"
CONSUL_DEFAULT_ADDRESS = "localhost:8500"
CONFIG_PATH = "/v1/kv/frances/config?raw"

class FrancesConfig:
  def __init__(self):
    self.defoe = None
    self.database = None

  @staticmethod
  def from_json(text):
    vals = json.loads(text)
    config = FrancesConfig()
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

def resolve_config():
  url = get_config_url()
  resp = requests.get(url)
  return FrancesConfig.from_json(resp.text)


config = resolve_config()
print(config.defoe.spark_url)
