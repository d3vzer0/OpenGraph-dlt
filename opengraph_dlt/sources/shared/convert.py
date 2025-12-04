from opengraph_dlt.sources.shared.models.graph import Graph, GraphEntries
import dlt


@dlt.transformer(columns=Graph, max_table_nesting=0)
def generate_graph(resources, model, apply_context=None, chunk_size: int = 1000):
    entries = GraphEntries(nodes=[], edges=[])
    for raw in resources:
        obj = model(**raw)
        if apply_context:
            apply_context(obj)
        if hasattr(obj, "as_node"):
            entries.nodes.append(obj.as_node)
        entries.edges.extend(obj.edges)
        if len(entries.nodes) + len(entries.edges) >= chunk_size:
            yield Graph(graph=entries)
            entries = GraphEntries(nodes=[], edges=[])
    if entries.nodes or entries.edges:
        yield Graph(graph=entries)
