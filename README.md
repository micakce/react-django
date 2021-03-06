# React + Django, docker-compose solution

In this tutorial we are going to build a containerized integration of React and
Django, and learn how to set up basic CRUD in Django backend.

This post is divided in two parts, __Part 1__ based on [this tutorial](https://dev.to/englishcraig/creating-an-app-with-docker-compose-django-and-create-react-app-31lf),
which is pretty much the containerization of the app, I will only reference the
commands used to get it working, cause the full and detailed explanation is in the original post.
__Part 2__ focuses on the CRUD configuration and its implementations details

__NOTE:__ The one problem I found with the Part1 tutorial, was that files created by
running a container command where created with the root user and group, I found myself
running `sudo chown myuser:myuser -R /created_folder` pretty often. To avoid that I
I included the solution explained in [this post](https://vsupalov.com/docker-shared-permissions/)
to my __Dockerfiles__

The folder structure for this project is as follows:
```bash
# $ tree <project_root>
.
├── backend
│   ├── <django_project>
│   ├── <django_app>
│   ├── db.sqlite3
│   ├── Dockerfile
│   ├── manage.py
│   └── requirements.txt
├── frontend
│   ├── Dockerfile
│   ├── node_modules
│   ├── package.json
│   ├── package-lock.json
│   ├── public
│   ├── README.md
│   ├── src
│   └── yarn.lock
├── docker-compose.yml
└── README.md
```


where `.` is the `<project_root>`, `<django_project>` is the main folder for the backend, and `<django_project>` is a
submodule/subapp of the backend, where we are going to configure the basic crud functionality

# Part 1

## 1.1 - Create a dockerized Django app

Let's start creating our Django container, for that we create the respective `Dockerfile`:

```Dockerfile
# <project_root>/backend/Dockerfile

# Use an official Python runtime as a parent image
FROM python:3

# set up container to create files with your current user
ARG USER_ID
ARG GROUP_ID

RUN addgroup --gid $GROUP_ID user
RUN adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID user

# Adding backend directory to make absolute filepaths consistent across services
WORKDIR /app/backend

# Install Python dependencies
COPY requirements.txt /app/backend
RUN pip3 install --upgrade pip -r requirements.txt

# Add the rest of the code
COPY . /app/backend

# Make port 8000 available for the app
EXPOSE 8000

# Install all dependencies with root user, then switch to the created user
USER user
# Be sure to use 0.0.0.0 for the host within the Docker container,
# otherwise the browser won't be able to find it
CMD python3 manage.py runserver 0.0.0.0:8000
```

In the terminal, run the following commands to build the image, create a Django
project named react_django_tut (<django_project>)
and run the app:

```bash
echo Django > server/requirements.txt
docker build -t backend:latest  \
            --build-arg USER_ID=$(id -u) \
            --build-arg GROUP_ID=$(id -g) backend
docker run -v $PWD/backend:/app/backend backend:latest django-admin startproject react_django_tut .
docker run -it -v $PWD/backend:/app/backend -p 8000:8000 backend:latest
```

Now go to `localhost:8000` and you should see Django welcome page.


## 1.2 - Create a dockerized React app with Create-React-App (CRA)

Do the same for the React container:

```Dockerfile
# <project_root>/frontend/Dockerfile

# Use an official node runtime as a parent image
FROM node:10

# set up container to create files with your current user
ARG USER_ID
ARG GROUP_ID
RUN addgroup --gid $GROUP_ID user
RUN adduser --disabled-password --gecos '' --uid $USER_ID --gid $GROUP_ID user

# install node_modules in different folder and point node to it (image portability)
WORKDIR /nm
# COPY ./package.json /nm
# RUN npm install
ENV NODE_PATH=/nm/node_modules
# change file ownership so you can install more packages as you develop
RUN chown -R user:user /nm

USER user

# main working directory
WORKDIR /app/frontend/

# Add rest of the client code
COPY . /app/frontend/

EXPOSE 3000

# CMD npm start
```

Given our concern of not creating the files with the root user, and also that running our
app with the root user doesn't seem right, we create a new folder where to
install the node_modules and define an environment variable to tell node where to find them,
the original post suggested a one-direction volume also called unnamed-volume for the
node_modules, but this messed our intent of running the container with a custom user. This
approach maintains image portability and adds a layer of security by not having to run the app
with the root user.

Some of the commands are currently commented out, because we don't have a few of
the files referenced, but we will need these commands later. Run the following
commands in the terminal to build the image, create the app, and run it:

```bash
docker build -t frontend:latest frontend \
            --build-arg USER_ID=$(id -u) \
            --build-arg GROUP_ID=$(id -g) .
docker run -v $PWD/frontend:/app/frontend frontend:latest npx create-react-app myProject
mv frontend/myProject/* frontend/myProject/.gitignore frontend/ && rmdir frontend/myProject
docker run -it -v $PWD/frontend:/app/frontend -p 3000:3000 frontend:latest npm start
```

Now should go to `localhost:3000` and be able to se the React welcome page


## 1.3 - "Docker-composify" into services with:

Creating the `docker-compose.yml` file:

```yaml
# <project_root>/docker-compose.yml

version: "3.2"
services:
    build:
      context: ./backend
      args:
        USER_ID: 1000
        GROUP_ID: 1000
    image: backend
    volumes:
      - ./backend:/app/backend
    ports:
      - "8000:8000"
    stdin_open: true
    tty: true
    command: python3 manage.py runserver 0.0.0.0:8000
  frontend:
    build:
      context: ./frontend
      args:
        USER_ID: 1000
        GROUP_ID: 1000
    image: frontend
    command: npm start
    volumes:
      - ./frontend:/app/frontend
      # One-way volume to use node_modules from inside image
      - /app/frontend/node_modules
    ports:
      - "3000:3000"
    stdin_open: true
    tty: true
    environment:
      - NODE_ENV=development
    depends_on:
      - backend
```

You might've noticed that in the docker-compose file I hard coded the ARG variables to
the user and group id of 1000, was the simplest thing to do given that everyone should
know their id when running the container, I found a few workarounds, but none of them worth it
for the sake of this post

Now you can uncomment the commands in the frontend/Dockerfile and run
`docker-compose build` and then `docker-compose up`, now you should be able
to see both welcome pages in their respective ports


## 1.4 - Connect Fronted with Backend

In order to allow communications between both services, we have to allow
__`backend`__ host in the Django configuration, specifically in the configuration file
__`backend/hello_world/settings.py`__, variable `ALLOWED_HOSTS`,

```python
# backend/hello_world/settings.py
# ...
ALLOWED_HOSTS = [
        'backend',
        ]
```

also modify the react package.json file to avoid CORS errors:
```javascript
# frontend/package.json
{
...
  "proxy": "http://backend:8000"
}
```


# Part 2
## 2.1 - Adding CRUD

In this part we'll be creating our db models, API routes and repective views
(logic behind this routes). We are going to create the subapp named basic_crud
(`<django_app>`) and configure the create/read/update/delete methods to handle the entries
in the db (in this example professors)

You can create a new Django app (which is kind of a subapp/module within the
Django project architecture) by running the following in the terminal (while
the container is running):

```bash
docker-compose exec backend python3 manage.py startapp basic_crud
# you have to restart the server so it detects the newly created files
docker-compose down
docker-compose up
```

### Models

1. First add your models in __`backend/<django_app>/models.py`__
```python
from django.db import models

class Professor(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    career = models.CharField(max_length=50)

    def __str__(self):
    '''Get the name of the professor when you print the object'''
        return self.first_name + ' ' + self.last_name
```

2. Add your app to the `INSTALLED_APPS` configuration in
`<project>/settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'basic_crud.apps.BasicCrud',
]

```
3. run `python manage.py makemigrations`
4. run `python manage.py migrate` (if you make any changes in your model, repeat 3 and 4)
5. To manage your new models in the Admin site, import and add them to the
`<django_app>/admin.py` file:

```python
from django.contrib import admin
from .models import Professor

admin.site.register(Professor)
```

<!-- ## Adding dependencies -->
<!-- ```bash -->
<!-- docker-compose exec frontend npm add axios -->
<!-- ``` -->

### Admin Site

To be able to login to the admin site you have to create a user, so attach to
you backend container `docker-compose exec backend /bin/bash` and run:
`python manage.py createsuperuser`. It al prompt for user name and password
(twice for confirmation), after this it'll be possibe  to login to the admin
site (`localhost:8000/admin`) and manage your models from there.

###  Requests

Now it is all ready to create your routes and add/get/edit/delete Professors from
the database, firts you need to know that urls are manage from
__`backend/<django_project>/urls.py`__ file, given we created an App and want
to manage this specific requests from there, we just include the basic_crud (<django_app>)
routes in this file and move on to configure the rest in the specific app configuration
file:

```python
from django.contrib import admin
from django.urls import include,path

urlpatterns = [
    # ...
    path('personnel/', include('<django_app>.urls'))
]
```

Django checks the incoming url request against the ones it has configured, what
this means is, when the incoming requests hit the path `personnel/` it'll go
check the configured urls in the <django_app> (module corresponding to that path).

Now we can move to our app and configure the rest there, we are going to focus
on two specific files: `<django_app>/urls.py`, where we configure our routes
and `<django_app>/views.py`, where we configure the logic that is going to be
executed when we hit those routes. I'll just explain the implementation of the
update (PUT) request, whose logic I had trouble the most, the rest is pretty much the
same just changing the request method

In the `<django_app>/urls.py` file:

```python
from django.urls import path

# we import the views, the ones that execute the logic
from . import views

# and add the url patter to the corresponding variable
urlpatterns = [
    # ...
    path('professor/<int:professor_id>/', views.get_professor, name='get_professor'),
    path('professor/edit/<int:professor_id>/', views.edit_professor, name='edit_professor'),
]
```

The path method takes 3 arguments, **the first argument** is the url pattern to match, the
<int:professor_id>, is a placeholder that indicates the url will have an
integer and that we can pass it as variable named `professor_id` to the view
method (see below in the view configuration). **The second argument**, is
simply the method from view that is going to be executed. **The third argument**,
allows us to set a name so it is easier to reference if we need to use it later
in the code (we don't get to make use of that in this tutorial).


In the `<django_app>/views.py` file:

```python
from django.core import serializers
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render,get_object_or_404
from django.forms.models import model_to_dict

# we gonna query the database, so we need the model
from .models import Professor
# json library used to (des)serialize data
import json

# Create your views here.

# ...

def get_professor(request, professor_id):
    if request.method == "GET":
        professor = get_object_or_404(Professor, pk=professor_id)
        # # Deserialize using serializers
        # prof_str = serializers.serialize('json', [professor])
        # prof_ser = prof_str[1:-1]
        # Deserialize using model_to_dict, (https://stackoverflow.com/questions/2391002/django-serializer-for-one-object)
        response = model_to_dict(professor)
        return JsonResponse(response)

def edit_professor(request, professor_id):
    if request.method == "PUT":
        data = json.loads(request.body)
        professor = get_object_or_404(Professor, pk=professor_id)
        first_name, last_name, career = [data[k] for k in ("first_name",
            "last_name", "career")]
        professor.first_name = first_name
        professor.last_name = last_name
        professor.career = career
        professor.save()
        return HttpResponse(f'Professor {professor} modified correctly')
```

There are the two functions executed when the corresponding URL is hit. You see
how the professor_id variable is passed as an argument, second to the request
object. We check that the request uses the correct method and query the database
accordingly. In order to send and receive json data, we have to (de)serialize
it. One thing that I couldn't find straightforward in the Django documentation was
how to serialize a single db object. I found two ways on internet (god
bless stack overflow). The first that is commented out, users the Django serializers class,
the solution was to surround with brackets the second argument, the second method makes
use of the Django model_to_dict method, pretty straightforward way of de-serializing a
single db object


## Coming next

Even tho we can do basic CRUD with the backed, until this point I tried it with
curl (see `<project_root>/request.sh`), next I'll be setting up the frontend to
display the data and do these operations from there.
