FROM runpod/worker:latest

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy handler
COPY . .

CMD ["python", "-u", "rp_handler.py"]
