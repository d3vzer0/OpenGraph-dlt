from opengraph_dlt.sources.dummy.models.random_data import RandomData
import dlt
import random


@dlt.source(name="dummy_opengraph")
def dummy_resources(*, resource_count: int = 10, node_count: int = 100):

    def generate_resource(resource_id: int):
        for _ in range(node_count):
            yield {"primary": random.random(), "secondary": random.random()}

    for resource_id in range(resource_count):
        yield dlt.resource(
            generate_resource(resource_id),
            columns=RandomData,
            name=f"random_data_{resource_id}",
        )
