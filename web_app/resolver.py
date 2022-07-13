from dataclasses import dataclass
from db import DatabaseConfig
from defoe import DefoeConfig
import os

CONSUL_VAR_NAME = "CONSUL_ADDRESS"
CONSUL_PROTOCOL = "http://"
CONSUL_DEFAULT_ADDRESS = "localhost:8500"
CONFIG_PATH = "/v1/kv/frances/config?raw"

@dataclass
class FrancesConfig:
  database: DatabaseConfig
  defoe: DefoeConfig


def resolve_config():
  url = get_config_url()


def get_config_url():
  consul_var = os.getenv(CONSUL_VAR_NAME)
  consul_address = None
  
  if consul_var != None:
    consul_address = consul_var
  else:
    consul_address = CONSUL_DEFAULT_ADDRESS
  
  return CONSUL_PROTOCOL + consul_address + CONFIG_PATH


def parse_config(text):
  return FrancesConfig()
