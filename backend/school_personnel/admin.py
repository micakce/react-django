from django.contrib import admin

from .models import Musician,Album,Person

# Register your models here.

admin.site.register(Musician)
admin.site.register(Album)
admin.site.register(Person)
