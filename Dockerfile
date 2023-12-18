FROM python:3.12.1-alpine3.18
WORKDIR /
ARG GITHUB_DEPENDENTS_INFO_VERSION=latest
ARG GITHUB_TOKEN

RUN pip install --no-cache-dir github-dependents-info

LABEL maintainer="Nicolas Vuillamy <nicolas.vuillamy@gmail.com>" \
      org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.revision=$BUILD_REVISION \
      org.opencontainers.image.version=$BUILD_VERSION \
      org.opencontainers.image.authors="Nicolas Vuillamy <nicolas.vuillamy@gmail.com>" \
      org.opencontainers.image.url="https://github.com/nvuillam/github-dependents-info" \
      org.opencontainers.image.source="https://github.com/nvuillam/github-dependents-info" \
      org.opencontainers.image.documentation="https://github.com/nvuillam/github-dependents-info" \
      org.opencontainers.image.vendor="Nicolas Vuillamy" \
      org.opencontainers.image.description="Generate markdown files with the list of dependent repositories of one or multiple packages of a single repository"

ENTRYPOINT ["github-dependents-info"]
