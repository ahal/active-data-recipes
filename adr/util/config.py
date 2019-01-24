import yaml


class Configuration(object):
    __slots__ = [
        "debug",
        "debug_url",
        "fmt",
        "list",
        "recipe",
        "url",
        "verbose",
    ]

    def __init__(self, yml_file=None):
        # No file: Empty config
        if yml_file:
            with open(yml_file, 'r') as content:
                cfg = yaml.load(content)
            self.update(cfg)
        # Init attribute if not exist in config file
        for key in Configuration.__slots__:
            if not hasattr(self, key):
                setattr(self, key, None)

    def update(self, config):
        """
        :param dict config: dictionary object of config
        """
        for key, value in config.items():
            # By pass non config key
            if key in Configuration.__slots__:
                setattr(self, key, value)

    def build_debug_url(self, query_id):
        """
        :param query_id:  query id
        :return: debug url with this query id
        """
        return self.debug_url.format(query_id)
