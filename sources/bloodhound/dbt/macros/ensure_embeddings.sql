{% macro ensure_embeddings_table() %}
    {% set database = target.database or 'lookup' %}
    {% set schema = target.schema %}
    -- CREATE SCHEMA IF NOT EXISTS {{ adapter.quote(database) }}.{{ adapter.quote(schema) }};

    CREATE TABLE IF NOT EXISTS {{ adapter.quote(database) }}.{{ adapter.quote(schema) }}.embeddings (
        object_id TEXT PRIMARY KEY,
        _dlt_id TEXT,
        embedding FLOAT[1024],
        _dlt_load_id TEXT
    );
{% endmacro %}
