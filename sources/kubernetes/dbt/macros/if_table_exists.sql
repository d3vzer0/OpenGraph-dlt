{% macro if_table_exists(source_name, table_name) %}
  {% if execute %}
    {% set relation = adapter.get_relation(
        database=target.database,
        schema=source(source_name, table_name).schema,
        identifier=table_name
    ) %}
    {% if relation is not none %}
      {% do return(true) %}
    {% else %}
      {% do return(false) %}
    {% endif %}
  {% else %}
    {% do return(false) %}
  {% endif %}
{% endmacro %}