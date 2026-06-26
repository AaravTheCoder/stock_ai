# Use an optimized, official Python 3.10 baseline image
FROM python:3.10-slim

# Set your working directory path straight to the app root folder
WORKDIR /app

# Copy over your package dependencies file first to save build cache tracks
COPY ./requirements.txt /app/requirements.txt

# Clean install all your deep learning frameworks and PyTorch CPU libraries
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy every remaining application and template folder asset into your live workspace
COPY . .

# Force the container environment to boot Gunicorn bound to port 7860
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]
