import dlt
from typing import Generator
from pathlib import Path
from enum import Enum
from dlt.sources.filesystem import read_parquet, read_csv, read_jsonl
from dlt.sources.filesystem import filesystem
from dlt.extract import DltResource
from typing import Any


class FileType(str, Enum):
    JSONL = "jsonl"
    PARQUET = "parquet"
    CSV = "csv"


FILETYPE_LOADERS: dict[FileType, Any] = {
    FileType.JSONL: read_jsonl,
    FileType.PARQUET: read_parquet,
    FileType.CSV: read_csv,
}


@dlt.source(name="resource_files", max_table_nesting=0)
def resource_files(
    root: Path,
    resource_names: list[str],
    glob: str = "**/*.jsonl.gz",
    file_type: FileType = FileType.JSONL,
) -> Generator[DltResource, None, None]:
    reader_source = filesystem(bucket_url=str(root), file_glob=glob)
    if file_type not in FileType:
        raise ValueError(f"Loader '{file_type}' not supported by filesystem readers")

    for resource in resource_names:
        reader = reader_source.add_filter(lambda item: (resource in item["file_url"]))
        yield (reader | FILETYPE_LOADERS[file_type]).with_name(resource)
