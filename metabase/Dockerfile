FROM metabase/metabase:v0.59.15 AS metabase-source

FROM eclipse-temurin:21-jre-jammy

WORKDIR /app

COPY --from=metabase-source /app /app

RUN groupadd --gid 2000 --system metabase \
    && useradd --uid 2000 --gid metabase --create-home --system metabase \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /plugins \
    && curl -L --retry 5 --retry-delay 5 \
       -o /plugins/duckdb.metabase-driver.jar \
       https://github.com/motherduckdb/metabase_duckdb_driver/releases/download/1.5.3.0/duckdb.metabase-driver.jar \
    && chmod 644 /plugins/duckdb.metabase-driver.jar \
    && chown -R metabase:metabase /plugins

ENV MB_PLUGINS_DIR=/plugins
ENV MB_JETTY_HOST=0.0.0.0

EXPOSE 3000

CMD ["/bin/bash", "-c", "exec java -XX:+IgnoreUnrecognizedVMOptions -Dfile.encoding=UTF-8 -Dlogfile.path=target/log -XX:+CrashOnOutOfMemoryError -server --add-opens java.base/java.nio=ALL-UNNAMED -jar /app/metabase.jar"]
