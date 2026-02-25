# Defines an ubuntu-based dev container for development and testing of pylibftdi

# As well as providing uv etc, this pre-installs the required libftdi1-2
# package, providing libftdi 1.5 (as of Ubuntu 24.04) and all its dependencies.

FROM ubuntu:24.04
WORKDIR /app

RUN \
  apt-get update && \
  apt-get install -y libftdi1-2 python3-minimal curl vim && \
  curl -LsSf https://astral.sh/uv/install.sh | sh

# Make uv available on PATH
ENV PATH="/root/.local/bin:$PATH"

CMD ["bash"]
