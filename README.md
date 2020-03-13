# React + Django, docker-compose solution

In this tutorial we are going to build a containerized integration of React and
Django. This post is based on [ this tutorial]( https://dev.to/englishcraig/creating-an-app-with-docker-compose-django-and-create-react-app-31l),
I'll just give you my comments on my experience.

Let's start creating out Django container, with the following `Dockerfile`:

## 1.- Create a dockerized Django app

```Dockerfile
# Use an official Python runtime as a parent image
FROM python:3

# Adding backend directory to make absolute filepaths consistent across services
WORKDIR /app/backend

# Install Python dependencies
COPY requirements.txt /app/backend
RUN pip3 install --upgrade pip -r requirements.txt

# Add the rest of the code
COPY . /app/backend

# Make port 8000 available for the app
EXPOSE 8000

# Be sure to use 0.0.0.0 for the host within the Docker container,
# otherwise the browser won't be able to find it
CMD python3 manage.py runserver 0.0.0.0:8000
```

In the terminal, run the following commands to build the image, create a Django project named hello_world, and run the app:

```bash
docker build -t backend:latest backend
docker run -v $PWD/backend:/app/backend backend:latest django-admin startproject hello_world .
docker run -v $PWD/backend:/app/backend -p 8000:8000 backend:latest
```

Now go to `localhost:8000` and you should see Django welcome page.


## 2.- Create a dockerized React app (With CRA)

```Dockerfile
# Use an official node runtime as a parent image
FROM node:10

WORKDIR /app/frontend/

# Install dependencies
# COPY package.json yarn.lock /app/frontend/

# RUN npm install

# Add rest of the client code
COPY . /app/frontend/

EXPOSE 3000

# CMD npm start
```
Some of the commands are currently commented out, because we don't have a few of
the files referenced, but we will need these commands later. Run the following
commands in the terminal to build the image, create the app, and run it:

```bash
docker build -t frontend:latest frontend
docker run -v $PWD/frontend:/app frontend:latest npx create-react-app myProject
mv frontend/hello-world/* frontend/hello-world/.gitignore frontend/ && rmdir frontend/hello-world
docker run -v $PWD/frontend:/app -p 3000:3000 frontend:latest npm start
```

Note that we move the newly-created app directory's contents up to the frontend
directory and remove it. Django gives us the option to do this by default, but
I couldn't find anything to suggest that CRA will do anything other than create
its own directory. Working around this nested structure is kind of a pain, so I
 find it easier to just move everything up the docker-service level and work
from there. Navigate your browser to `localhost:3000` to make sure the app is
running. Also, you can uncomment the rest of the commands in the Dockerfile,
so that any new dependencies will be installed the next time you rebuild the image.


## 3.- "Docker-composify" into services with:

```yaml
version: "3.2"
services:
  backend:
    build: ./backend
    image: backend
    volumes:
      - ./backend:/app/backend
    ports:
      - "8000:8000"
    stdin_open: true
    tty: true
    command: python3 manage.py runserver 0.0.0.0:8000
  frontend:
    build: ./frontend
    image: frontend
    command: npm start
    volumes:
      - ./frontend:/app/frontend
      # One-way volume to use node_modules from inside image
      - /app/frontend/node_modules
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - MY_DJANGO_PROJECT=react_django
    depends_on:
      - backend
```

Now, run `docker-compose up` and you should be able to see both welcome pages
again in their corresponding URLs, if you get an error you might need to do
`docker-compose build` and then `docker-compose up`, and now it should be ready
to go, you have your containers ready to go


## 4 .- Connect Fronted with Backend

In order to allow communications between both services, we have to allow
__`backend`__ host in Django configuration (ALLOWED\_HOSTS) in __`backend/hello_world/settings.py`__
and also add __"proxy": "http://backend:8000"__ to the `package.json` file.


## 5.- Adding CRUD

Let's start by creating an API route for the frontend to call. You can create a
new Django app (which is kind of a sub-app/module within the Django project
architecture) by running the following in the terminal:
`docker-compose run --rm backend python3 manage.py startapp char_count` if the
container is stopped or `docker exec ${name-of-container} -it python3 manage.py
startapp school_personnel` if it is running

## Adding dependencies
```bash
docker-compose run --rm frontend npm add axios
docker-compose down
docker-compose up --build
```
