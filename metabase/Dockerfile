FROM metabase/metabase:latest

USER root
RUN mkdir -p /plugins \
    && curl -L --retry 5 --retry-delay 5 \
       -o /plugins/duckdb.metabase-driver.jar \
       https://github.com/MotherDuck-Open-Source/metabase_duckdb_driver/releases/latest/download/duckdb.metabase-driver.jar \
    && chmod 644 /plugins/duckdb.metabase-driver.jar

ENV MB_PLUGINS_DIR=/plugins