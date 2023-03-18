class KGUrlsConfig:
    def __init__(self):
        eb = ""
        chapbooks = ""

    @staticmethod
    def from_dict(vals):
        config = KGUrlsConfig()
        config.eb = vals["eb"]
        config.chapbooks = vals["chapbooksScotland"]
        return config
