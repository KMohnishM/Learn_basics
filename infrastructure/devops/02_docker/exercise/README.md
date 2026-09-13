# Module 2 Exercise: Containerizing a Legacy Database App

You have just been hired at a new company. They have a legacy Node.js application that currently runs directly on an old Linux server. It crashes often because of environment issues. 

Your manager has asked you to containerize the application and set up a local development environment using Docker Compose so other developers can run it easily.

## The Challenge

Inside this `exercise/` folder, you will find `server.js` and `package.json`. This is the Node.js application. It connects to a PostgreSQL database.

Your task:
1. **Write a `Dockerfile`**: It should use an official Node image (e.g., `node:18-alpine`), copy the app files, run `npm install`, expose port `3000`, and start the app with `npm start`.
2. **Write a `docker-compose.yml`**: It should define two services:
   - `web`: Built from your new Dockerfile. It should map host port `8080` to container port `3000`. It depends on the database.
   - `db`: Use the official `postgres:15-alpine` image. You MUST pass environment variables to it (`POSTGRES_USER=myuser`, `POSTGRES_PASSWORD=secret`, `POSTGRES_DB=mydb`) so the Node app can connect.
   - **Crucially**: Add a Docker Volume to the `db` service so that database data is not lost when the container is stopped.

## Hints
- In `server.js`, you'll see it tries to connect to a database host named `db`. This means your postgres service in docker-compose *must* be named `db` so Docker's internal DNS routes it correctly.

Good luck! When you are finished, check the `solution/` folder.
