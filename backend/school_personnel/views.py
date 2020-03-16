from django.core import serializers
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render,get_object_or_404
from django.forms.models import model_to_dict


from .models import Professor
import json

# Create your views here.



def index(request):
    return JsonResponse({"message": "Index responding"})

def get_all(request):
    response = serializers.serialize("json", Professor.objects.all())
    return HttpResponse(response)

def get_professor(request, professor_id):
    if request.method == "GET":
        professor = get_object_or_404(Professor, pk=professor_id)

        # # Deserialize using serializers
        # prof_str = serializers.serialize('json', [professor])
        # prof_ser = prof_str[1:-1]

        # Deserialize using model_to_dict, (https://stackoverflow.com/questions/2391002/django-serializer-for-one-object)
        response = model_to_dict(professor)

        return JsonResponse(response)

def add_professor(request):
    if request.method == "POST":
        professor = json.loads(request.body)
        first_name = professor["first_name"]
        last_name = professor["last_name"]
        career = professor["career"]
        new_professor = Professor(first_name=first_name, last_name=last_name,
                career=career)
        new_professor.save()
        return HttpResponse(f'Professor {new_professor} has been created correctly')

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

def delete_professor(request, professor_id):
    professor = get_object_or_404(Professor, pk=professor_id)
    professor.delete()
    return HttpResponse(f'Professor {professor} deleted correctly')
