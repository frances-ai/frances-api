class FilesConfig:
  def __init__(self):
    self.uploads_path = ""
    self.results_path = ""
    self.models_path = ""
    self.images_path = ""
  
  @staticmethod
  def from_dict(vals):
    config = FilesConfig()
    config.uploads_path = vals["uploads"]
    config.results_path = vals["results"]
    config.models_path = vals["models"]
    config.images_path = vals["images"]
    return config
