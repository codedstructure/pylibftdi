# Defines an ubuntu-based dev container for development and testing of pylibftdi

# As well as providing poetry etc, this pre-installs the required libftdi1-2
# package, providing libftdi 1.5 (as of Ubuntu 24.04) and all its dependencies.

FROM ubuntu:24.04
WORKDIR /app
RUN \
  apt-get update; \
  apt-get install -y libftdi1-2 python3-minimal python3-pip python3-poetry vim;

# Use in-project venvs so subsequent `poetry install` operations are quick
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
# Required for `poetry shell` to detect the shell
ENV SHELL=/bin/bash

CMD ["bash"]
