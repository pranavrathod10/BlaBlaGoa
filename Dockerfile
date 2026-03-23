# Step 1 — Choose the base image
# This is a slim Python 3.13 image — just enough to run Python, nothing extra
FROM python:3.13-slim

# Step 2 — Set the working directory inside the container
# All commands from here on run inside /app
WORKDIR /app

# Step 3 — Copy requirements first (before copying your code)
# This is a performance trick — Docker caches layers
# If requirements.txt hasn't changed, Docker skips reinstalling packages
COPY requirements.txt .

# Step 4 — Install dependencies
# --no-cache-dir keeps the image smaller (no pip cache needed in a container)
RUN pip install --no-cache-dir -r requirements.txt

# Step 5 — Copy your application code
COPY ./app ./app
COPY alembic/ alembic/
COPY alembic.ini .
COPY startup.sh .

# Step 6 — Tell Docker which port your app listens on
# This is documentation — doesn't actually open the port
EXPOSE 8000

# Step 7 — The command to run when the container starts
# Note: no --reload in production, that's development only
CMD ["./startup.sh"]