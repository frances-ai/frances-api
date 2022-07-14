import json
from json import JSONEncoder
from dataclasses import dataclass


output_fields = {}


class Response:
  def __init__(self):
    self.success = True
    self.error = ""
  
  def encode(self):
    return ResponseEncoder().encode(self)


@dataclass
class Pagination:
  page: int
  total: int
  per_page: int
  search: int


@dataclass
class TermSearchResponse(Response):
  results: dict
  pagination: Pagination
  headers: dict
  term: str
  # bar_plot: str
  # heatmap_plot: str


@dataclass
class DetailsResponse(Response):
  details: dict
  

@dataclass
class VisualizationResponse(Response):
  results: dict
  uri: str


@dataclass
class SpellCheckResponse(Response):
  results: dict
  definition: str
  clean_definition: str


class ResponseEncoder(JSONEncoder):
  def default(self, obj):
    fields = obj.__dict__
    output = {}
    for key, val in fields.items():
      new_key = self.as_output_name(key)
      output[new_key] = val
    return output
  
  @staticmethod
  def as_output_name(name):
    if name in output_fields:
      return output_fields[name]
    
    upper_flag = False
    output = ""
    for c in name:
      if c == "_":
        upper_flag = True
        continue
      if upper_flag:
        output += c.upper()
      else:
        output += c
      upper_flag = False
    
    output_fields[name] = output
    return output


if __name__ == "__main__":
  r = TermSearchResponse(
    results = {
      "abc": "bfg",
    },
    pagination = Pagination(5, 100, 5, False), 
    headers = {
      "abc": "bfg",
    },
    term = "searchstuff"
    )
  print(ResponseEncoder().encode(r))
