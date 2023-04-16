FROM python:3.10.11-bullseye


#updates
RUN apt-get update && apt-get upgrade -y

# Set the working directory to /app
WORKDIR /app

# Copy the requirements.txt file into the container at /app
COPY requirements.txt ./requirements.txt

# Install dependencies
RUN pip install -r requirements.txt


# Copy the current directory contents into the container at /app
COPY . .

# Sets the permissions for the app directory
RUN chmod -R 755 /app

# Start the app
CMD ["python3", "-m" ,"discordBot.py"]

