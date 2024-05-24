FROM python:3.12-slim


WORKDIR /changeguard

COPY . /changeguard
RUN apt-get -y update && \
  apt-get -y --no-install-recommends install git=1:2.39.2-1.1 xxhash=0.8.1-1 && \
  apt-get -y clean && \
  apt-get -y autoremove && \
  rm -rf /var/lib/apt/lists/* && \
  useradd -m -d /home/user -s /bin/bash user && \
  pip install --no-cache-dir --upgrade pip setuptools wheel && \
  mkdir -p /home/user/.local && \
  chown -R user:user /changeguard /home/user/.local && \
  chmod -R a+wrX /changeguard && \
  git config --global --add safe.directory /data



USER user
WORKDIR /changeguard
ENV PATH=/home/user/.local/bin:$PATH
ENV PYTHONPATH=/home/user/.local/lib/python3.12/site-packages
RUN git config --global --add safe.directory /data && \
  pip install --no-cache-dir --prefix=/home/user/.local .

# This is where the user will mount their data to.
WORKDIR /data

ENTRYPOINT ["python", "-m", "changeguard.cli"]
CMD ["--help"]
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -m changeguard.cli --version || exit 1
