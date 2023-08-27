from pytest_factoryboy import register

from tests.factories import TagFactory, TagColorFactory

pytest_plugins = "tests.fixtures"

register(TagColorFactory)
register(TagFactory)
