from django.db import models

# Create your models here.

# Client model that stores client_id, first_name, and last_name
class Client(models.Model):
    client_id = models.AutoField(primary_key = True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    def __str__(self):
        return str(self.client_id) + ' ' + self.first_name + ' ' + self.last_name

# Provider model that stores provider_id, first_name, and last_name
class Provider(models.Model):
    provider_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    def __str__(self):
        return  str(self.provider_id) + ' ' + self.first_name + ' ' + self.last_name

# Timeslot model that stores the timeslot_id, provider (foreign key), first_name, last_name, start_time,
# end_time, and is_available (whether the timeslot can be booked). I think this model could have been
# created without the first_name and last_name since we have the foreign key to the provider table,
# but I was thinking it would be easier for the frontend to display information and for logging the
# released timeslots in case of an expired reservation if we included first_name and last_name
class TimeSlot(models.Model):
    timeslot_id = models.AutoField(primary_key=True)
    provider = models.ForeignKey('Provider', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_available = models.BooleanField()

    def __str__(self):
        return  str(self.timeslot_id) + ' ' + str(self.provider.provider_id) + ' ' + self.first_name + ' ' + self.last_name + ' ' + str(self.start_time) + ' -- ' + str(self.end_time) + ' ' + str(self.is_available)

# Reservation model that stores the reservation_id, timeslot (foreign key), provider (foreign key),
# client (foreign key), start_time, end_time, created_at, and is_confirmed. I think this model could
# have maybe been combined with the timeslot model. However, we would have had to have dummy or null
# values for the client_id and created_at until a reservation was made. In addition, queries to the
# combined object might have been a little complicated so to simplify things I separated them into
# two different models
class Reservation(models.Model):
    reservation_id = models.AutoField(primary_key = True)
    timeslot = models.ForeignKey('Timeslot', on_delete=models.CASCADE)
    provider = models.ForeignKey('Provider', on_delete=models.CASCADE)
    client = models.ForeignKey('Client', on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField()
    is_confirmed = models.BooleanField()

    def __str__(self):
        return str(self.reservation_id) + ' ' + str(self.timeslot.timeslot_id) + ' ' + str(self.provider.provider_id) + ' ' + str(self.client.client_id) + ' '+ str(self.start_time) + ' -- ' + str(self.end_time) + ' ' + str(self.created_at) + ' ' + str(self.is_confirmed)
