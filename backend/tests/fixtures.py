import pytest

from recipes.models import Tag
from tests.factories import TagFactory


@pytest.fixture()
def tags():
    """Generates recipe tags."""
    TagFactory.create_batch(size=5)

    return Tag.objects.all()
