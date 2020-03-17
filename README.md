# React + Django, docker-compose solution

In this tutorial we are going to build a containerized integration of React and
Django, and learn how to set up basic CRUD in Django backend.

This post is divided in two parts, __Part 1__ based on [this tutorial](https://dev.to/englishcraig/creating-an-app-with-docker-compose-django-and-create-react-app-31lf),
which is pretty much the containerization of the app, I will only reference the
commands used to get it working, cause the explanation is in the original post.
__Part 2__ focuses on the CRUD configuration and its implementations details

The folder structure for this project is as follows:
```bash
.
├── backend
│   ├── db.sqlite3
│   ├── Dockerfile
│   ├── manage.py
│   ├── requirements.txt
│   └── school_personnel
├── frontend
│   ├── Dockerfile
│   ├── frontend
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

# Part 1

## 1.1 - Create a dockerized Django app

Let's start creating out Django container, with the following `Dockerfile`:

```Dockerfile
# <project_root>/backend/Dockerfile

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

In the terminal, run the following commands to build the image, create a Django
project named <django_project>  (in this tutorial it is basic_crud_tut )
and run the app:

```bash
docker build -t backend:latest backend
docker run -v $PWD/backend:/app/backend backend:latest django-admin startproject hello_world .
docker run -v $PWD/backend:/app/backend -p 8000:8000 backend:latest
```

Now go to `localhost:8000` and you should see Django welcome page.


## 1.2 - Create a dockerized React app (With CRA)

Do the same for the React container:

```Dockerfile
# <project_root>/frontend/Dockerfile

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

Now should go to `localhost:3000` and be able to se the React welcome page


## 1.3 - "Docker-composify" into services with:

Creating the following file:

```yaml
# <project_root>/docker-compose.yml

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
    depends_on:
      - backend
```

Now, run `docker-compose up` and you should be able to see both welcome pages
again in their corresponding URLs, if you get an error you might need to do
`docker-compose build` and then `docker-compose up`, and now it should be ready
to go.


## 1.4 - Connect Fronted with Backend

In order to allow communications between both services, we have to allow
__`backend`__ host in Django configuration in the configuration file
__`backend/hello_world/settings.py`__, variable `ALLOWED\_HOSTS`, also add
__"proxy": "http://backend:8000"__ to the `/frontend/package.json` file.


# Part 2
## 2.1 - Adding CRUD

In this part we'll be creating our db models, API routes and repective views
(logic behind this routes). We are gonna create a `school_personnel` app and
going to be creating, reading, updating a deleting professors from the db.

You can create a new Django app (which is kind of a sub-app/module within the
Django project architecture) by running the following in the terminal (while
the container is running):

```
docker-compose exec backend python3 manage.py startapp <django_app>
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
        return self.first_name + ' ' + self.last_name

```

2. Add your app to the `INSTALLED_APPS` configuration in
`<project>/settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'school_personnel.apps.SchoolPersonnelConfig',
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
to manage this specific requests from there, we just include the <django_app>
routes in this file and move on ro configure the rest in the specific app:

```python
from django.contrib import admin
from django.urls import include,path

urlpatterns = [
    # ...
    path('personnel/', include('<django_app>.urls'))
]
```

Django checks the incoming url request against the ones it has configured, what
this means is, when the incoming requests have the path `personnel/` it'll go
check the configured urls in the <django_app> module.

Now we can move to our app and configure the rest there, we are going to focus
on two specific files: `<django_app>/urls.py`, where we configure our routes
and `<django_app>/views.py`, where we configure the logic that is going to
execute when we hit those routes. I'll just explain the implementation of the
update (PUT) request, whose logic I had trouble the most.

In the `<django_app>/urls.py`file:
```
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

The path method takes 3 arguments: the first one is url pattern to match, the
<int:professor_id>, is a placeholder that indicates the url will have an
integer and that we can pass it as variable named `professor_id` to the view
method (see below in the view configuration). **The second argument**, is
simply the method from view that is going to execute. **The third argument**,
allows us to set a name so it is easier to reference if we need to use it later
in the code (out of the scope of this tutorial).


In the `<django_app>/views.py`file:

```python
from django.core import serializers
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render,get_object_or_404
from django.forms.models import model_to_dict

# we gonna query the database, so we need the model
from .models import Professor
# used to (des)serialize data
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

There are the two functions executed when the corresponding URL is hit. You se
how the professor_id variable is passed as an argument, second to the request
object. We check the request uses the correct method and query the database
accordingly. In order to send and receive json data, we have to (des)serialize
it. One thing that I could find strighforward in the Django documentation was
how to serialize a single a sigle db object. Found two ways on internet (god
bless stack overflow), I leave the links so you chenck them out


## Coming next

Even tho we can do basic CRUD with the backed, until this point I tried it with
curl (see `<project_root>/request.sh`), next I'll be setting up the frontend to
diplay the data and do these operations from there.
