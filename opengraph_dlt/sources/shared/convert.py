from opengraph_dlt.sources.shared.models.graph import Graph, GraphEntries
from collections import deque
import dlt


@dlt.transformer(columns=Graph, max_table_nesting=0)
async def generate_graph(resources, model, apply_context=None, chunk_size: int = 1000):
    entries = GraphEntries(nodes=[], edges=[])
    edges = deque()
    for raw in resources:
        obj = model(**raw)
        if apply_context:
            apply_context(obj)
        if hasattr(obj, "as_node"):
            entries.nodes.append(obj.as_node)

        # Or this
        # all_edges = await obj.edges
        edges.extend(obj.edges)

        # async for edge in obj.edges:
        #     edges.append(edge)

        if len(entries.nodes) + len(entries.edges) >= chunk_size:
            # entries.edges = list(edges)
            yield Graph(graph=entries)
            entries = GraphEntries(nodes=[], edges=[])
    if entries.nodes or entries.edges:
        # entries.edges = list(edges)
        yield Graph(graph=entries)
