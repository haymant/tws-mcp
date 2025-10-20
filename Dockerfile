FROM python:3.11-slim

# Install uv
RUN pip install uv

WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY main.py ./

# Install dependencies
RUN uv sync --frozen

# Expose server port
EXPOSE 8000

# Run the server
CMD ["uv", "run", "python", "main.py"]
