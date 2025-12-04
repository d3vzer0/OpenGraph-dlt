from opengraph_dlt.sources.dummy.models.random_person import RandomPerson
from faker import Faker
import dlt


@dlt.source(name="dummy_opengraph")
def dummy_resources(*, resource_count: int = 10, node_count: int = 100):

    fake = Faker()

    def generate_resource(resource_id: int):
        for _ in range(node_count):
            yield {"name": fake.name(), "address": fake.address()}

    for resource_id in range(resource_count):
        yield dlt.resource(
            generate_resource(resource_id),
            columns=RandomPerson,
            name=f"random_person_{resource_id}",
        )
