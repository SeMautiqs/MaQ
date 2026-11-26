# Docker image for the MaQ# artifact.
#
# Build from the root of the repository (with the as4qc submodule checked out):
#   docker build -f artifact/Dockerfile -t maqsharp:spin27 .
#
# Everything needed at run time is installed while building, so the container
# does not need network access.
FROM ubuntu:25.04

ARG MAUDE_VERSION=3.5.1
ARG MAUDE_SHA256=72ed1ca87e3b3d0dfc6ee1436baf154bf04c45ff97d521bec040c5e8dfc8f92c
ARG QDK_VERSION=1.34.0
# samples and Quantum Katas of the Q# repository, used for the coverage of existing code
ARG QSHARP_COMMIT=0e58afc2fbb3fb8db806412b045acc0c675f8ce3

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl git unzip python3 python3-pip \
 && rm -rf /var/lib/apt/lists/*

# Maude (official Linux release)
RUN curl -fsSL -o /tmp/maude.zip \
      https://github.com/maude-lang/Maude/releases/download/Maude${MAUDE_VERSION}/Maude-${MAUDE_VERSION}-linux-x86_64.zip \
 && echo "${MAUDE_SHA256}  /tmp/maude.zip" | sha256sum -c - \
 && mkdir -p /opt/maude && unzip -q /tmp/maude.zip -d /opt/maude \
 && chmod +x /opt/maude/maude && rm /tmp/maude.zip

# Microsoft Quantum Development Kit, used only by the validation script
RUN pip3 install --no-cache-dir --break-system-packages qdk==${QDK_VERSION}

RUN git init -q /opt/qsharp && cd /opt/qsharp \
 && git remote add origin https://github.com/microsoft/qsharp.git \
 && git fetch -q --depth 1 origin ${QSHARP_COMMIT} && git checkout -q FETCH_HEAD \
 && rm -rf .git

ENV PATH=/opt/maude:$PATH \
    MAUDE_LIB=/opt/maude \
    QSHARP_PYTHON_TELEMETRY=none

COPY . /MaQ
RUN test -f /MaQ/common/as4qc/cpx.maude \
 || (echo "as4qc is missing: run 'git submodule update --init' before building" && false)

WORKDIR /MaQ/maqsharp
CMD ["bash"]
