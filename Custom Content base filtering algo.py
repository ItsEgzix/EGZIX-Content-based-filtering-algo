
""" this is a custom algo for conetent based filtering for car rental systems developed by egzix"""

def analyze_user_preferences(user):
    bookings = Booking.objects.filter(user=user)
    
    if not bookings.exists():
        return None

    avg_price = bookings.aggregate(Avg('car__price'))['car__price__avg']
    avg_seats = bookings.aggregate(Avg('car__seats'))['car__seats__avg']
    favorite_type = bookings.values('car__car_type').annotate(count=Count('car__car_type')).order_by('-count').first()['car__car_type']
    
    return {
        'avg_price': avg_price,
        'avg_seats': avg_seats,
        'favorite_type': favorite_type
    }

def closest_seat_count(avg_seats):
    ''' Takes the average seats prefered by the user and returns the closest available no of seats '''
    SEAT_CHOICES = [2, 4, 6]
    return min(SEAT_CHOICES, key=lambda x: abs(x - avg_seats))

def smart_search(user, latitude=None, longitude=None, max_distance=None):
    preferences = analyze_user_preferences(user)

    if preferences is None:
        return None  # Return all cars if no past bookings
    else:
        closest_seats = closest_seat_count(preferences['avg_seats'])

        cars = Car.objects.filter(
            price__lte=preferences['avg_price'] * 1.2,  # x1.2 for some flexibility
            seats=str(closest_seats),
            car_type=preferences['favorite_type']
        )
    
    if latitude is not None and longitude is not None:
        latitude = float(latitude)
        longitude = float(longitude)
        
        cars = cars.annotate(
            distance=ExpressionWrapper(
                6371.0 * ACos(
                    Cos(Radians(latitude)) * Cos(Radians(F('latitude'))) * Cos(Radians(F('longitude')) - Radians(longitude)) +
                    Sin(Radians(latitude)) * Sin(Radians(F('latitude')))
                ),
                output_field=FloatField()
            )
        ).order_by('distance')
        
        if max_distance is not None:
            cars = cars.filter(distance__lte=max_distance)
    return cars