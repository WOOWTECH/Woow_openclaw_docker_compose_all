FROM python:3.9-slim

WORKDIR /app

# Install ttyd + kubectl at build time (not runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates \
    && curl -Lo /usr/local/bin/ttyd \
        https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64 \
    && chmod +x /usr/local/bin/ttyd \
    && KUBECTL_VER=$(curl -Ls https://dl.k8s.io/release/stable.txt) \
    && curl -Lo /usr/local/bin/kubectl \
        "https://dl.k8s.io/release/${KUBECTL_VER}/bin/linux/amd64/kubectl" \
    && chmod +x /usr/local/bin/kubectl \
    && apt-get purge -y curl && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 18790 7681

CMD ["python", "entrypoint.py"]
