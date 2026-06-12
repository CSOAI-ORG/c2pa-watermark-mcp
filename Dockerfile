FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY requirements.txt pyproject.toml README.md ./
RUN pip install --no-cache-dir -e .

# Copy the source
COPY c2pa_watermark_mcp/ ./c2pa_watermark_mcp/
COPY tests/ ./tests/

# Re-install in case the editable install didn't pick up everything
RUN pip install --no-cache-dir -e .

# Expose for stdio MCP — Vercel uses the api/ entry point, but the
# container can also run as a standalone stdio MCP server.
EXPOSE 8000

# Default: run the stdio MCP server
CMD ["python", "-m", "c2pa_watermark_mcp.server"]
