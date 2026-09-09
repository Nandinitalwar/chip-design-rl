FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends iverilog bash coreutils && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY repo/ /app/
