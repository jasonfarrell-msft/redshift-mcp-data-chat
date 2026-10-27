# Official Python tag/index and linux/amd64 manifest verified 2026-10-26.
FROM python:3.13.17-slim-trixie@sha256:d98cc29d3266e535dd9da1099688d9cb3ca4753813571e071763d17725460962 AS wheel
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /build
COPY requirements-build.lock ./
RUN python -m pip install --require-hashes --only-binary=:all: -r requirements-build.lock
COPY pyproject.toml README.md ./
COPY redshift_mcp_server/*.py ./redshift_mcp_server/
RUN python -m pip wheel --no-deps --no-build-isolation --wheel-dir /wheels .

FROM python:3.13.17-slim-trixie@sha256:d98cc29d3266e535dd9da1099688d9cb3ca4753813571e071763d17725460962
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN python -m venv /opt/adapter && python -m venv /opt/official
ENV PATH="/opt/adapter/bin:$PATH"
COPY requirements.lock ./
RUN python -m pip install --require-hashes --only-binary=:all: -r requirements.lock
COPY requirements-official.lock ./
RUN /opt/official/bin/python -m pip install --require-hashes --only-binary=:all: -r requirements-official.lock
COPY aws-config ./
COPY --from=wheel /wheels/ /wheels/
RUN python -m pip install --no-deps /wheels/*.whl \
    && rm -rf /wheels \
    && groupadd --gid 10001 mcp \
    && useradd --uid 10001 --gid mcp --no-create-home --home-dir /app mcp
USER 10001:10001
EXPOSE 8000
CMD ["redshift-mcp-server", "--host", "0.0.0.0", "--port", "8000"]
