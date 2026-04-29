# Use Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose port if needed (though Telegram bots don't listen on ports)
# EXPOSE 8000

# Command to run the bot
CMD ["python", "bot.py"]