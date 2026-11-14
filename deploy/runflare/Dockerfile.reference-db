# Build as its own Runflare Docker service; no application secrets in the image.
# PostgreSQL 17 matches the local reference database. Mount persistent storage
# at /var/lib/postgresql/data and set POSTGRES_* using Runflare secrets.
FROM pgvector/pgvector:0.8.7-pg17
ENV PGDATA=/var/lib/postgresql/data/pgdata
# Match the Docker application's available port choices in this Runflare panel.
# PostgreSQL still speaks its native TCP protocol, not HTTP.
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --retries=10 \
    CMD pg_isready -p 8000 -U "$POSTGRES_USER" -d "$POSTGRES_DB"
CMD ["postgres", "-p", "8000"]
