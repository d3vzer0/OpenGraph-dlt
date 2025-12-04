from opengraph_dlt.sources.shared.convert import generate_graph
from opengraph_dlt.sources.dummy.models.random_data import RandomData
from dlt.sources.filesystem import filesystem as filesystemsource, read_jsonl
import dlt


@dlt.source(name="dummy_opengraph")
def dummy_opengraph(
    *,
    resource_count: int = 10,
    bucket_url: str = dlt.config.value,
    chunk_size: int = dlt.config.value,
):

    for resource_id in range(resource_count):
        table = f"random_data_{resource_id}"
        reader = (
            filesystemsource(bucket_url=bucket_url, file_glob=f"{table}/**/*.jsonl.gz")
            | read_jsonl()
        ).with_name(f"{table}_fs")

        yield (reader | generate_graph(RandomData, chunk_size=chunk_size)).with_name(
            f"{table}_fs_graph"
        )
