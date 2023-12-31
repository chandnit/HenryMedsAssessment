from django.contrib import admin
from .models import Client, Provider, Reservation, TimeSlot

admin.site.register(Client)
admin.site.register(Provider)
admin.site.register(TimeSlot)
admin.site.register(Reservation)
