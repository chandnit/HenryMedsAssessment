# HenryMedsAssessment
Build a Reservation System API for Clients and Providers

## Initial Setup
#### Note: I set this project up on a Mac and used python3 for all my commands before I activated the virtual env. If you are setting up on Linux or Windows be sure to use the correct command for your system (e.g. python vs python3).
1. Download the latest version of python from https://www.python.org/downloads/
2. Check you have the latest version doing ```python3 —-version```
3. Download the project into your directory of preference
4. Once in the project folder, go into the top-level reservation_system folder with ```cd reservation_system```
5. Create a virtual env so your dependencies don’t affect anything else outside this folder with the command ```python3 -m venv env```
6. Activate the virtual env with ```source env/bin/activate```
7. Install the dependencies with ```pip install -r requirements.txt```
8. Setup your database tables by running the following 2 commands in order: ```python manage.py makemigrations``` and then ```python manage.py migrate```
9. Pre-populate the db with 2 clients and 2 providers by running ```python manage.py loaddata prepopulate_db.json```
10. Run the server with ```python manage.py runserver```

You are now ready to use the API. I will take some time to talk about each endpoint below and the design decisions I've made. For your convenience, I've also included a Postman collection which has all the endpoints configured correctly in a file called ```Henry Meds Assessment Endpoints.postman_collection.json```.

#### Note: The server ip will be listed when you run command 10. You will need to add this to the URL before any endpoint you hit. I've taken care of this in the Postman collection, but if you decide to use something else you would need something like this: ```127.0.0.1:8000/provider/availability``` .

## Endpoints
### POST provider/create

This creates a new provider. This requires a first name and last name in the body and I am assuming that whoever uses this endpoint makes sure to include those values. If I had more time and I wanted to get this production ready, I would add in some input validations for those two fields.

Input:

```
{
  "first_name": “John”,
  "last_name": “Doe”
}
```
Returns a newly created provider with a provider_id. You can hit this endpoint before proceeding with testing the others or just use the providers I prepopulate the database with in the initial setup:
```
{
    "provider_id": 1,
    "first_name": "John",
    "last_name": "Doe"
}
```

### POST client/create 

This creates a new client. This requires a first name and last name in the body and I am assuming that whoever uses this endpoint makes sure to include those values. If I had more time and I wanted to get this production ready, I would add in some input validations for those two fields.

Input:

```
{
  "first_name": "Harry",
  "last_name": "Potter"
}
```
Returns a newly created client with a client_id. You can hit this endpoint before proceeding with testing the others or just use the clients I prepopulate the database with in the initial setup:
```
{
    "client_id": 1,
    "first_name": "Harry",
    "last_name": "Potter"
}
```

### POST provider/availability 

This endpoint allows a provider to post their availability. The input requires a provider_id, start_time, and end_time; the time range is in ISO format in the request body. Again, here I assume a valid provider_id, start_time, and end_time are supplied. I also assume the availability can only occur in 15 minute multiples (e.g. HH:15, HH:30) and the start_time and end_time provided are also a 15 minute multiple. If I had more time and I wanted to get this production ready, I would add in some input validations as well as allow the provider to submit their availability in a more user-friendly format.

Input:

```
{
    "provider_id": 1, 
    "start_time": "2023-12-30T10:00:00", 
    "end_time": "2023-12-30T11:30:00"
    
}
```
Given the start_time and end_time, this endpoint calculates the 15 min timeslots and stores them in a Timeslot table in the database. It then returns the created timeslots:

```
{
    "available timeslots": [
        {
            "timeslot_id": 1,
            "provider_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "start_time": "2023-12-30T10:00:00Z",
            "end_time": "2023-12-30T10:15:00Z",
            "is_available": true
        },
        {
            "timeslot_id": 2,
            "provider_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "start_time": "2023-12-30T10:15:00Z",
            "end_time": "2023-12-30T10:30:00Z",
            "is_available": true
        },
        {
            "timeslot_id": 3,
            "provider_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "start_time": "2023-12-30T10:30:00Z",
            "end_time": "2023-12-30T10:45:00Z",
            "is_available": true
        },
        {
            "timeslot_id": 4,
            "provider_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "start_time": "2023-12-30T10:45:00Z",
            "end_time": "2023-12-30T11:00:00Z",
            "is_available": true
        }
    ]
}
```

A feature that would be nice to have for production would be allowing timeslots of different lengths. Different types of appointments require different lengths of time so it would be nice to include that here. Another feature we could think about adding would be to allow a provider to submit multiple ranges of availability (For example if they wanted to block some time off for lunch). Finally, a third feature could be allowing a provider to remove timeslots in case something urgent comes up and they need to either block off time to handle the issue or cancel the rest of the timeslots for the day.

### GET /client/getProviderAvailability?provider_id=id

This endpoint allows a client to get a provider's availability given a provider_id. Here, I am assuming the provider_id supplied in the URL is a valid provider_id. Within the method I do two checks before displaying the availability to the client. I call an internal function that gets all the reservations that weren't confirmed and were made more than 30 min ago. I then go through and delete those reservations as they are expired and release the timeslots. Once this is done, I make sure that out of all the timeslots available, I filter out the timeslots whose start time is less than 24 hrs from now. Reservations must be made 24 hrs in advance so showing these timeslots to the client would be a waste. I then return the available timeslots to the user. All times are converted to UTC before any comparisons are done.

An example URL input:

```127.0.0.1:8000/client/getProviderAvailability?provider_id=1```

Returns:

```
{
    "available timeslots": [
        {
            "timeslot_id": 1,
            "provider_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "start_time": "2023-12-30T10:00:00Z",
            "end_time": "2023-12-30T10:15:00Z",
            "is_available": true
        },
        {
            "timeslot_id": 2,
            "provider_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "start_time": "2023-12-30T10:15:00Z",
            "end_time": "2023-12-30T10:30:00Z",
            "is_available": true
        },
        {
            "timeslot_id": 3,
            "provider_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "start_time": "2023-12-30T10:30:00Z",
            "end_time": "2023-12-30T10:45:00Z",
            "is_available": true
        },
        {
            "timeslot_id": 4,
            "provider_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "start_time": "2023-12-30T10:45:00Z",
            "end_time": "2023-12-30T11:00:00Z",
            "is_available": true
        }
    ]
}
```

### PUT /provider/expiredReservations
Although we delete any expired reservations and make the timeslots available for the client to book again in ```getProviderAvailiablity```, deleting and writing to the database before showing available timeslots in a production-ready system with millions of users might end up being a bottleneck. 

To overcome this I wrote this endpoint which essentially calls the same internal function, deletes any reservations older than 30 min that weren't confirmed, releases the timeslots, and returns them as output. The only difference is this endpoint returns the released timeslots for logging purposes whereas in the ```getProviderAvailability``` endpoint, we run another filter so I suppress showing available timeslots until the very end. All times are converted to UTC before any comparisons are done.

My idea for the production-ready system would be to have a scheduled job that runs periodically (every n minutes) that calls this endpoint and removes those expired reservations, making the timeslots available again. This would significantly reduce the number of writes and deletes on the ```getProviderAvailability``` endpoint, reducing the bottleneck on the system.

Returns:
```
{
    "Expired reservations deleted and corresponding timeslots released": [
        {
            "timeslot_id": 4,
            "provider_id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "start_time": "2023-12-30T10:45:00Z",
            "end_time": "2023-12-30T11:00:00Z",
            "is_available": true
        }
    ]
}
```

### POST /client/reserve
This endpoint requires a client_id and timeslot_id and returns a scheduled reservation. Here I am assuming the client_id supplied is for an existing client and the timeslot_id is for an existing timeslot. If I had more time and I wanted to get this production ready, I would add in some input validations for those two fields. 

Some error checking I implemented was to return an error message when a client tries to reserve a timeslot that is unavailable. This could happen in the case that they call the ```getProviderAvailability``` endpoint and then call the current endpoint with some delay. During that time, someone else could have booked the same timeslot. Another scenario where a timeslot could be unavailable is if one of the expired reservations had a timeslot with a start_time less than 24 hours away. Ideally, they shouldn't have access to this timeslot_id as the is_available field will remain false and wouldn't show up when ```getProviderAvailability``` was called.

Another error check that I implemented is to make sure the timeslot start_time is greater than 24 hrs from now. Reservations must be made 24 hrs in advance and although I check this in ```getProviderAvailability``` for the timeslot, if there is a delay in calling this endpoint, this error could still occur. In production, we could provide some leniency here (within 5 min of the 24 hr window) since the client was in the process of booking a reservation. 

All times are converted to UTC before any comparisons are done.

Input:

```
{
    "client_id": 1, 
    "timeslot_id": 4
    
}
```
Returns the scheduled reservation and sets the created_at time to the current time. The is_confirmed field is set to false and finally, the timeslot is made unavailable to prevent other users from seeing it when they call ```getProviderAvailability```.

```
{
    "Reservation scheduled": {
        "reservation_id": 3,
        "timeslot_id": 4,
        "provider_id": 1,
        "client_id": 1,
        "start_time": "2023-12-30T07:05:00Z",
        "end_time": "2023-12-30T11:00:00Z",
        "created_at": "2023-12-29T07:04:16",
        "is_confirmed": false
    }
}
```
Another idea for invalidating expired reservations in production would be implementing some sort of distributed messaging queue system. Once the reservation has been created it is pushed onto a queue with a time-delayed response (30 min) to check the status of the is_confirmed field. If during that time, the reservation is confirmed then the value can be updated in the database. Finally, when the 30 min is up, the reservation is pulled out of the queue and the reservation_id is compared to the reservation_id in the database. If it is marked as confirmed in the databse, then all is good; if not, the reservation is deleted and the timeslot is released. Some tools we can consider using for this could be RabbitMQ, Apache Pulsar, etc.

### PUT /client/confirm

This endpoint requires a client_id and reservation_id and returns a confirmed reservation. Here I am assuming the client_id is for an existing client and I also check to make sure the reservation_id is valid. If I had more time and I wanted to get this production ready, I would add in some input validations for the client_id.

Error checks implemented:

-- If someone tries to confirm the reservation using a client_id different from the one on the reservation.

-- If someone tries to confirm a reservation that has already been confirmed.

-- If someone tries to confirm a reservation and the time now is 30 min greater than when the reservation was created, I delete the reservation and make the timeslot available again with a message to the client. This is again part of the strategy of spreading out the writes and deletes as much as possible so it doesn't cause too much strain on the ```getProviderAvailability``` endpoint. All times are converted to UTC before any comparisons are done.

Input:

```
{
    "client_id": 1, 
    "reservation_id": 6
    
}
```
Returns a confirmed reservation:

 ```
{
    "Reservation is confirmed": {
        "reservation_id": 6,
        "timeslot_id": 3,
        "provider_id": 1,
        "client_id": 1,
        "start_time": "2023-12-30T10:30:00Z",
        "end_time": "2023-12-30T10:45:00Z",
        "created_at": "2023-12-29T09:27:51Z",
        "is_confirmed": true
    }
}
```

## Final Thoughts
Although I've elaborated in each endpoint description what I would change/add to make this project ready for production, I want to finish with some design decisions that I would make on the system as a whole:

For the database tables (schema located in models.py), we currently keep every entry ever created except for the Reservation table where we delete scheduled reservations that have expired. In a production environment with millions of users, this might not be feasible and may not make much business sense. If a provider or client leaves our system, it might make sense to keep their information in the database for some time (ex: 6 months), before getting rid of it. Similarly, for timeslots or confirmed reservations in the past, we might keep them around for a bit for analytics purposes and then get rid of them. By creating some sort of cleanup job that runs every so often, we could keep our database costs low and make querying the database that much faster. Alternatively, if we want to keep the data around, we could move it to a separate read-only database to perform analytics on. In this case, we could add a status field to our Reservation table schema and mark scheduled reservations that have expired as 'EXPIRED' instead of deleting them.

Another issue that can occur in production, is when two clients try to reserve the same provider timeslot at the same time. We could handle this concurrency issue by implementing some sort of optimistic locking where each timeslot has an additional field for version_number in the database. The client would pull the timeslot in the endpoint ```/client/reserve``` and when is_available is changed to false while booking, we could also update the version number. We could then check to see if the version number getting written back to the database exceeds the current version number by 1. For example, if two clients both want to book 10:00-10:15 timeslot for a provider, they pull that timeslot from the database and it has the version v1. Client A finishes his transaction first and writes back to the database with v2 and it succeeds. Client B tries to write back v2 as well but sees the current version number in the database is v2, so we gracefully return an error to Client B.

Another thing I would add for production would be a full test suite including unit testing, integration testing, regression testing, performance testing, and stress testing to name a few. Also, I would like to have the QA or the engineering team perform end-to-end testing from the frontend to the backend, making sure to test each possible outcome.

Adding in authentication would also be important for a production-ready system, as well as making sure only authorized providers/clients are allowed to make changes for their specific endpoints.

Finally, we will want to build a distributed, fault-tolerant system that can handle millions of users. When the requests come in from the users we can have a load balancer that could distribute the API calls between our two services based on the URL: provider service and client service. Each of these services could have multiple instances to distribute the workload. From there we would have our database with multiple instances as well. We would have to employ some sort of sharding with a good hashing algorithm to make sure the data is distributed evenly so that one server's load doesn't become a bottleneck. Another optimization we could do would be to add a cache for frequent read requests of the database, making our response time to the users much faster. In the background, we could have an async job that runs periodically to update any writes from the database to the cache. There could also be a couple of scheduled jobs associated with the database: One to clear the expired reservations, and another to write data to a read-only analytics database and remove it from our main database. If we decide to use a message queue to invalidate expired reservations, this can live between the client service and the database and could work as described in the ```/client/reserve``` endpoint. The design I described above is one of many potential ones we could use. We could build everything from scratch, but with so many tools out there to build distributed systems we should leverage these before committing to bulding anything custom.
