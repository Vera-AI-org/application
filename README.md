# Vera-AI API

This is a base project for a FastAPI application that uses a PostgreSQL database, all orchestrated with Docker and Docker Compose to provide a simplified development environment.

## Prerequisites

Before getting started, make sure you have the following tools installed on your machine:

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Getting Started

Follow the steps below to set up and run the development environment.

### 1. Set Up Environment Variables

The project uses a `.env` file to manage database credentials and other configurations. You can create your own from the sample file:

```bash
cp .env_sample .env
```

The default variables in `.env_sample` are already configured to work with the `docker-compose.yml` file. You can change them if you like, but for a first run, the defaults should work fine.

### 2. Start the Containers

With Docker running on your machine, use Docker Compose to build the application image and start the services (API and database):

```bash
docker-compose up --build
```

The `--build` flag forces the image to rebuild, which is useful if you've made changes to the code or the `Dockerfile`.

### 3. Access the Application

Once everything is up and running, the application will be available at the following addresses:

- **API**: http://localhost:8000  
- **Interactive Documentation (Swagger UI)**: http://localhost:8000/docs  
- **Alternative Documentation (ReDoc)**: http://localhost:8000/redoc  

The PostgreSQL database will be accessible on port `5432` of your local machine (`localhost`).

## Stopping the Application

To stop and remove the containers, run the following command in your terminal:

```bash
docker-compose down
```