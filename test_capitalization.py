"""Test capitalization implementation"""

from apps.api.domain.user import User, UserId
from apps.api.domain.events import EventRecord
from apps.api.domain.geocoding import PlaceResult
from uuid import UUID

# Test User capitalization
user = User(
    id=UserId(value=UUID('12345678-1234-5678-1234-567812345678')),
    email='test@example.com',
    display_name='john doe',
    hashed_password='hashed',
    role='researcher',
    status='active',
    created_at='2024-01-01',
    updated_at='2024-01-01'
)
print(f'User display_name: {user.display_name}')
assert user.display_name == 'John Doe', f'Expected "John Doe", got "{user.display_name}"'

# Test EventRecord capitalization
event = EventRecord(
    id=UUID('12345678-1234-5678-1234-567812345678'),
    chart_id=UUID('12345678-1234-5678-1234-567812345678'),
    event_date='2024-01-01',
    title='marriage ceremony',
    user_id=UUID('12345678-1234-5678-1234-567812345678')
)
print(f'Event title: {event.title}')
assert event.title == 'Marriage Ceremony', f'Expected "Marriage Ceremony", got "{event.title}"'

# Test PlaceResult capitalization
place = PlaceResult(
    display_name='new york city',
    latitude=40.7128,
    longitude=-74.0060,
    country='USA'
)
print(f'Place display_name: {place.display_name}')
assert place.display_name == 'New York City', f'Expected "New York City", got "{place.display_name}"'

print('All tests passed!')