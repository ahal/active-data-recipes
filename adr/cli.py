from __future__ import absolute_import, print_function

import logging
import os
import sys
import time
import webbrowser
from argparse import ArgumentParser

from adr.formatter import all_formatters
from adr.query import format_query
from adr.recipe import run_recipe
from adr.util.config import Configuration

here = os.path.abspath(os.path.dirname(__file__))

log = logging.getLogger('adr')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())

RECIPE_DIR = os.path.join(here, 'recipes')
QUERY_DIR = os.path.join(here, 'queries')


class RecipeParser(ArgumentParser):

    def __init__(self, config, **kwargs):
        super(RecipeParser, self).__init__(
              description='Run an adr recipes.', conflict_handler='resolve', **kwargs)

        self.config = config
        self._recipes = None
        self._queries = None

        # Build the main parser.
        self._add_args(self, args=[
                (['recipe'],
                    {'nargs': '?', 'default': None,
                     'help': "Name of the recipe to run."}),
                (['-l', '--list'],
                    {'action': 'store_true', 'default': False,
                     'help': "List available recipes or queries."}),
                (['-f', '--format'],
                    {'default': self.config.fmt, 'choices': list(all_formatters.keys()),
                     'help': "Format to print data in (default: table)."}),
                (['-v', '--verbose'],
                    {'action': 'store_true', 'default': self.config.verbose,
                     'help': "Print the raw query and other debugging information."}),
                (['--url'],
                    {'default': self.config.url, 'help': "Url of ActiveData endpoint."}),
                (['-h', '--help'],
                    {'action': 'store_true',
                     'help': "Type --help to get help. Type <recipe> --help "
                             "to get help with a recipe."}),
        ])
        self.set_defaults(func=recipe_handler)

        # Build the `query` subparser.
        subparsers = self.add_subparsers(parser_class=ArgumentParser)
        query_parser = subparsers.add_parser('query', help='Run a query directly.')
        self._add_args(query_parser, args=[
            (['query'],
                {'nargs': '?', 'default': None,
                 'help': "Name of the query to run."}),
            (['--debug'],
                {'action': 'store_true', 'default': config.debug,
                 'help': "Open a query in ActiveData query tool."}),
        ])
        query_parser.set_defaults(func=query_handler)

    def _add_args(self, parser, args=None):
        for flags, options in args or []:
            parser.add_argument(*flags, **options)

    def parse_known_args(self, *args, **kwargs):
        args, remainder = super(RecipeParser, self).parse_known_args(*args, **kwargs)
        self.validate(args)

        if args.help:
            return self._help(args)

        return args, remainder

    def validate(self, args):
        if hasattr(args, 'query') and args.query not in self.queries:
            self.error("query '{}' not found!".format(args.query))

        if args.recipe and args.recipe not in self.recipes:
            self.error("recipe '{}' not found!".format(args.recipe))

    @property
    def recipes(self):
        if self._recipes:
            return self._recipes

        self._recipes = [os.path.splitext(item)[0] for item in os.listdir(
                         RECIPE_DIR) if item != '__init__.py' and item.endswith('.py')]
        return self._recipes

    @property
    def queries(self):
        if self._queries:
            return self._queries

        self._queries = [os.path.splitext(item)[0] for item in os.listdir(
                         QUERY_DIR) if item.endswith('.query')]
        return self._queries

    def _help(self, args):
        recipe = args.recipe
        if not recipe:
            self.print_help()
            sys.exit(0)

        print('Usage for adr ' + recipe + ':')
        run_recipe(recipe, ['--help'], self.config)


def query_handler(args, remainder, config):
    """Runs, formats and prints queries.

    All functionality remains same as adr.query:cli.

    :param Namespace args: Namespace object produced by main().
    :param list remainder: List of unknown arguments.
    :param Configuration config: config object
    """
    if args.list:
        log.info('\n'.join(sorted(queries)))
        return

    data, url = format_query(query, config)
    print(data)
    if url:
        time.sleep(2)
        webbrowser.open(url, new=2)


def recipe_handler(config, remainder):
    """Runs recipes.

    :param Configuration config: Config objects
    :param list remainder: List of unknown arguments.
    """
    recipe = config.recipe
    print(run_recipe(recipe, remainder, config))


def main(args=sys.argv[1:]):
    """Entry point for the adr module.

    When the adr module is called, this method is run.

    The argument list is parsed, and the appropriate parser or subparser is created.

    Using the argument list, arguments are parsed and grouped into a Namespace object
    representing known arguments, and a remainder list representing unknown arguments.

    The method then calls the appropriate method for the action specified.

    Supported use cases:

    $ adr recipe <recipe_name>
    $ adr query <query_name>
    $ adr <recipe_name>

    :param list args: command-line arguments.
    """
    # load config from file
    config = Configuration(os.path.join(here, 'config.yml'))

    # create parsers and subparsers.
    parser = RecipeParser(config)

    # parse all arguments, then pass to appropriate handler.
    args, remainder = parser.parse_known_args()

    if args.list:
        if args.query:
            print("\n".join(sorted(parser.queries)))
            return
        print("\n".join(sorted(parser.recipes)))
        return

    # store all non-recipe/query args into config
    # From this point, only config stores all non-recipe/query args
    # Additional args will go to remainder
    config.update(vars(args))
    log.setLevel(logging.DEBUG) if config.verbose else log.setLevel(logging.INFO)

    return args.func(config, remainder)


if __name__ == '__main__':
    sys.exit(main())
