class FilesConfig:
  def __init__(self):
    uploads_path = ""
    results_path = ""
  
  @staticmethod
  def from_dict(vals):
    config = FilesConfig()
    config.uploads_path = vals["uploads"]
    config.results_path = vals["results"]
    return config
