from rest_framework import serializers
from .models import Client, Provider, TimeSlot, Reservation

# Serializers to convert model objects into JSON
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['client_id', 'first_name', 'last_name']

class ProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Provider
        fields = ['provider_id', 'first_name', 'last_name']

class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['timeslot_id', 'provider_id', 'first_name', 'last_name', 'start_time', 'end_time', 'is_available']

class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['reservation_id', 'timeslot_id', 'provider_id', 'client_id', 'start_time', 'end_time', 'created_at', 'is_confirmed']
