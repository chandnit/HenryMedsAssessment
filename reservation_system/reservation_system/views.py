import datetime
import pytz

from .models import Client, Provider, TimeSlot, Reservation
from .serializers import  (ClientSerializer, ProviderSerializer, TimeSlotSerializer,
                           ReservationSerializer)
from rest_framework.decorators import  api_view
from rest_framework.response import Response
from rest_framework import status
import json
from dateutil import parser


# This creates a new provider. This requires a first name and last name in the body, and
# I am assuming that whoever uses this endpoint makes sure to include those values.
# Returns a newly created provider with their provider_id.
@api_view(['POST'])
def add_provider(request):
    serializer = ProviderSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status = status.HTTP_201_CREATED)

# This creates a new client. This requires a first name and last name in the body, and
# I am assuming that whoever uses this endpoint makes sure to include those values.
# Returns a newly created client with their client_id
@api_view(['POST'])
def add_client(request):
    serializer = ClientSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status = status.HTTP_201_CREATED)


# This endpoint allows a provider to post their availability. The input requires a provider_id,
# start_time, and end_time; the time range is in ISO format in the request body. Again, here I
# assume a valid provider_id, start_time, and end_time are supplied. I also assume the availability
# can only occur on 15 minute multiples (e.g. HH:15, HH:30) and the start_time and end_time provided
# are also a 15 minute multiple.
@api_view(['POST'])
def add_availability(request):
    raw_body = json.loads(request.body)
    provider_id = int(raw_body.get('provider_id'))
    start_time = parser.parse(raw_body.get('start_time'))
    end_time = parser.parse(raw_body.get('end_time'))
    timeslots = __calculate_availability(provider_id, start_time, end_time)
    serializer = TimeSlotSerializer(timeslots, many=True)
    return Response({'available timeslots': serializer.data}, status=status.HTTP_201_CREATED)

# Internal function that calculates the 15 min appointment slots given the start_time and end_time.
# It then uses the provider_id and stores them in the Timeslot table in the database.
def __calculate_availability(provider_id, start_time, end_time):
    delta = datetime.timedelta(minutes=15)
    timeslots = []
    while start_time < end_time:
        stop_time = delta + start_time
        provider_object = Provider.objects.get(provider_id = provider_id)
        timeslot = TimeSlot(provider= provider_object, first_name = provider_object.first_name,
                            last_name = provider_object.last_name,  start_time = start_time,
                            end_time =stop_time, is_available = True)
        timeslots.append(timeslot)
        timeslot.save()
        start_time = stop_time
    return timeslots

# This endpoint allows a client to get a provider's availability given a provider_id. Here I
# am assuming the provider_id supplied in the URL is a valid provider_id for an existing provider.
@api_view(['GET'])
def get_provider_availability(request):
   provider_id = request.GET.get("provider_id")
   # Deletes reservations that aren't confirmed and older than 30 mins and makes the timeslots
   # available. All times are converted to UTC before any comparisons are done.
   __release_reservation_slots()
   now = (parser.parse(datetime.datetime.now().replace(microsecond=0).isoformat())
          .replace(tzinfo=pytz.UTC))
   # Only shows timeslots for a specific provider that are available and the start_time
   # is greater than or equal to the current time + 24 hrs as reservations must be made
   # 24 hrs in advance so showing those other timeslots to the client would be a waste.
   # All times are converted to UTC before any comparisons are done.
   timeslots = TimeSlot.objects.filter(provider = int(provider_id), is_available = True,
                                       start_time__gte = now + datetime.timedelta(hours=24))
   serializer = TimeSlotSerializer(timeslots, many=True)
   return Response({'available timeslots': serializer.data}, status=status.HTTP_200_OK)

@api_view(['PUT'])
# Deletes reservations that aren't confirmed and older than 30 mins and makes the timeslots
# available. All times are converted to UTC before any comparisons are done. This returns a list
# of timeslots now available for logging purposes. For a production-ready system we could have a
# scheduled job that runs periodically (every n minutes) that calls this endpoint to clear the
# expired reservations to reduce the strain on endpoint above.
def clean_expired_reservations(request):
    clean = True
    timeslots = __release_reservation_slots(clean)
    serializer = TimeSlotSerializer(timeslots, many=True)
    return Response({'Expired reservations deleted. Available timeslots:':serializer.data},
                    status=status.HTTP_200_OK)

# Uses the current time and deletes any reservations that aren't confirmed and were made more than
# 30 min ago. It then makes the timelsot associated with that reservation available again. All times are
# converted to UTC before any comparisons are done
def __release_reservation_slots(clean = False):
    now = (parser.parse(datetime.datetime.now().replace(microsecond=0).isoformat())
           .replace(tzinfo=pytz.UTC))
    reservations = Reservation.objects.filter(is_confirmed = False,
                                              created_at__lt = now - datetime.timedelta(minutes=30))
    timeslots = []
    if reservations.exists():
        for r in reservations:
            timeslot = TimeSlot.objects.get(timeslot_id = r.timeslot.timeslot_id)
            # If the timeslot start_time is greater than 24 hrs of the current time, then we mark it as
            # available. Otherwise, we can keep is_available as false as the client should not be allowed
            # to book it
            if timeslot.start_time > now + datetime.timedelta(hours=24):
                timeslot.is_available = True
                timeslots.append(timeslot)
                timeslot.save()
            r.delete()
        if clean:
            return timeslots


# This endpoint creates a scheduled reservation using the client_id and timeslot_id. Here I am assuming
# the client_id supplied is for an existing client and the timeslot_id is for an existing timeslot.
# If I had more time and I wanted to get this production ready I would add in some input validations
# for those two fields. All times are converted to UTC before any comparisons are done
@api_view(['POST'])
def make_reservation(request):
    raw_body = json.loads(request.body)
    client_id = int(raw_body.get('client_id'))
    timeslot_id = int(raw_body.get('timeslot_id'))
    timeslot = TimeSlot.objects.get(timeslot_id = timeslot_id)

    # If the user is trying to book an unavailable timeslot we want to return a helpful error message
    # to the client.
    if timeslot.is_available == False:
        return Response('Timeslot is unavailable. Please choose a different one',
                        status=status.HTTP_401_UNAUTHORIZED)

    provider = Provider.objects.get(provider_id = timeslot.provider.provider_id)
    client = Client.objects.get(client_id = client_id)
    created_at = datetime.datetime.now().replace(microsecond=0).isoformat()

    # If the current time plus 24 hrs is greater than the start time, we return an error saying
    # reservations must be made 24 hrs in advance.
    if (parser.parse(created_at).replace(tzinfo=pytz.UTC) + datetime.timedelta(hours=24) >
            timeslot.start_time.replace(tzinfo=pytz.UTC)):
        return Response('Reservations must be made 24 hrs in advance',
                        status=status.HTTP_401_UNAUTHORIZED)

    reservation = Reservation(timeslot =timeslot, provider = provider, client = client,
                              start_time = timeslot.start_time, end_time = timeslot.end_time,
                              created_at =created_at,
                              is_confirmed = False)
    reservation.save()
    # timeslot is invalidated here to prevent it showing up for anyone else
    timeslot.is_available = False
    timeslot.save()
    serializer = ReservationSerializer(reservation)
    return Response({'Reservation scheduled': serializer.data}, status=status.HTTP_200_OK)

# This endpoint requires a client_id and reservation_id and returns a scheduled reservation. Here
# I am assuming the client_id  is for an existing client and I also check to make sure the
# reservation_id is valid. If I had more time and I wanted to get this production ready I would
# add in some input validations for the client_id. All times are converted to UTC before any
# comparisons are done
@api_view(['PUT'])
def confirm_reservation(request):
    raw_body = json.loads(request.body)
    client_id = int(raw_body.get('client_id'))
    reservation_id = int(raw_body.get('reservation_id'))
    # Have to use .filter here despite at most 1 item returned as .get doesn't allow for empty values.
    reservations = Reservation.objects.filter(reservation_id = reservation_id)
    # Checks for valid reservation_id or error message is returned.
    if reservations.exists():
        reservation = reservations[0]
        # The client_id on the reservation has to match up with the one sent in the request.
        if reservation.client.client_id != client_id:
            return Response('The client_id does not match with the one in the reservation',
                            status=status.HTTP_403_FORBIDDEN)

        # If the reservation is already confirmed, we shouldn't have to do anything. Return an error
        # message to the client.
        elif reservation.is_confirmed == True:
            return Response('Reservation has already been confirmed',
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            now = (parser.parse(datetime.datetime.now().replace(microsecond=0).isoformat())
                   .replace(tzinfo=pytz.UTC))
            # If more than 30 min have passed since the reservation was created, then delete the
            # reservation and make the timeslot available.
            if now > reservation.created_at.replace(tzinfo=pytz.UTC) + datetime.timedelta(minutes=30):
                timeslot = TimeSlot.objects.get(timeslot_id=reservation.timeslot.timeslot_id)
                timeslot.is_available = True
                timeslot.save()
                reservation.delete()
                return Response('More than 30 min since reservation was made. '
                                'Reservation is being released', status=status.HTTP_400_BAD_REQUEST)
            else:
                reservation.is_confirmed = True
                reservation.save()
                serializer = ReservationSerializer(reservation)
                return Response({'Reservation is confirmed': serializer.data},
                                status=status.HTTP_200_OK)
    else:
        return Response('Invalid reservation_id',
                        status=status.HTTP_400_BAD_REQUEST)