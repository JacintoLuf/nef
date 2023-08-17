#It instructs Docker Engine to use official python:3.10 as the base image
FROM python:3.10

#It creates a working directory(server) for the Docker image and container
WORKDIR /server

#It copies the script into the working directory
COPY echo_udp_server.py .

#It will expose the script on port `8000` inside the container
EXPOSE 8000

#It is the command that will start and run the script container
CMD ["python", "echo_udp_server.py", "-p=80"]