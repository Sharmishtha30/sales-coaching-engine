FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir . && useradd -m coach && mkdir -p /app/data && chown -R coach:coach /app
USER coach
ENV COACH_DATA_DIR=/app/data
EXPOSE 8000
CMD ["uvicorn", "sales_coach.api:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
