FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir .
USER 10001
EXPOSE 8080
CMD ["uvicorn","journey_agent.api:app","--host","0.0.0.0","--port","8080"]
