import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.permissions import GATE_OPERATOR_GROUP, PARKING_ADMIN_GROUP
from parkings.models import ParkingLot, ParkingSpace, ParkingSpaceType, Tariff
from reservations.models import Reservation
from vehicles.models import Vehicle


DEMO_PASSWORD = 'DemoPass123!'


class Command(BaseCommand):
    help = 'Create safe demo data for the parking system.'

    def handle(self, *args, **options):
        admin_group, _ = Group.objects.get_or_create(name=PARKING_ADMIN_GROUP)
        operator_group, _ = Group.objects.get_or_create(name=GATE_OPERATOR_GROUP)

        users = self.create_demo_users(admin_group, operator_group)
        space_types = self.create_space_types()
        parkings = self.create_parkings()
        spaces = self.create_spaces(parkings, space_types)
        tariffs = self.create_tariffs(parkings, space_types)
        vehicles = self.create_vehicles(users['user'])
        self.create_reservations(users['user'], vehicles, spaces, tariffs)

        self.stdout.write(self.style.SUCCESS('Demo data is ready.'))
        self.stdout.write('')
        self.stdout.write('Demo users:')
        self.stdout.write(f'  admin_demo / {DEMO_PASSWORD}')
        self.stdout.write(f'  operator_demo / {DEMO_PASSWORD}')
        self.stdout.write(f'  user_demo / {DEMO_PASSWORD}')
        self.stdout.write('')
        self.stdout.write('Main demo URLs:')
        self.stdout.write('  /')
        self.stdout.write('  /about/')
        self.stdout.write('  /parkings/')
        self.stdout.write('  /parkings/search/')
        self.stdout.write('  /accounts/profile/')
        self.stdout.write('  /vehicles/')
        self.stdout.write('  /dashboard/')
        self.stdout.write('  /reports/')
        self.stdout.write('  /access-control/')
        self.stdout.write('  /access-control/logs/')

    def create_demo_users(self, admin_group, operator_group):
        User = get_user_model()

        admin, _ = User.objects.get_or_create(
            username='admin_demo',
            defaults={
                'email': 'admin_demo@example.com',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        admin.email = 'admin_demo@example.com'
        admin.is_staff = True
        admin.is_superuser = True
        admin.set_password(DEMO_PASSWORD)
        admin.save()
        admin.groups.add(admin_group)

        operator, _ = User.objects.get_or_create(
            username='operator_demo',
            defaults={
                'email': 'operator_demo@example.com',
                'is_staff': True,
            },
        )
        operator.email = 'operator_demo@example.com'
        operator.is_staff = True
        operator.is_superuser = False
        operator.set_password(DEMO_PASSWORD)
        operator.save()
        operator.groups.add(operator_group)
        operator.groups.remove(admin_group)

        user, _ = User.objects.get_or_create(
            username='user_demo',
            defaults={
                'email': 'user_demo@example.com',
                'is_staff': False,
            },
        )
        user.email = 'user_demo@example.com'
        user.is_staff = False
        user.is_superuser = False
        user.set_password(DEMO_PASSWORD)
        user.save()
        user.groups.remove(admin_group, operator_group)

        return {
            'admin': admin,
            'operator': operator,
            'user': user,
        }

    def create_space_types(self):
        data = [
            ('Стандартне', 'Звичайне паркомісце для легкового автомобіля.'),
            ('Електромобіль', 'Місце для електромобіля.'),
            ('Для людей з інвалідністю', 'Паркомісце з пріоритетним доступом.'),
        ]

        return {
            name: ParkingSpaceType.objects.get_or_create(
                name=name,
                defaults={
                    'description': description,
                    'is_active': True,
                },
            )[0]
            for name, description in data
        }

    def create_parkings(self):
        data = [
            {
                'name': 'Demo Parking Center',
                'address': 'м. Київ, вул. Демонстраційна, 10',
                'description': 'Центральна демонстраційна парковка для захисту дипломної роботи.',
                'latitude': Decimal('50.450100'),
                'longitude': Decimal('30.523400'),
            },
            {
                'name': 'Demo Parking Campus',
                'address': 'м. Київ, просп. Освітній, 5',
                'description': 'Навчальна парковка з різними типами паркомісць.',
                'latitude': Decimal('50.444000'),
                'longitude': Decimal('30.520000'),
            },
        ]

        parkings = {}

        for item in data:
            parking, _ = ParkingLot.objects.get_or_create(
                name=item['name'],
                defaults=item,
            )

            for field, value in item.items():
                setattr(parking, field, value)

            parking.is_active = True
            parking.save()
            parkings[parking.name] = parking

        return parkings

    def create_spaces(self, parkings, space_types):
        spaces = {}

        grid_config = {
            'Demo Parking Center': (3, 4),
            'Demo Parking Campus': (2, 4),
        }

        type_cycle = [
            space_types['Стандартне'],
            space_types['Стандартне'],
            space_types['Електромобіль'],
            space_types['Для людей з інвалідністю'],
        ]

        for parking_name, (rows, columns) in grid_config.items():
            parking = parkings[parking_name]

            for row in range(1, rows + 1):
                row_label = chr(ord('A') + row - 1)

                for column in range(1, columns + 1):
                    number = f'{row_label}{column}'
                    space_type = type_cycle[(column - 1) % len(type_cycle)]
                    is_active = not (parking_name == 'Demo Parking Campus' and row == rows and column == columns)

                    space, _ = ParkingSpace.objects.get_or_create(
                        parking_lot=parking,
                        number=number,
                        defaults={
                            'space_type': space_type,
                            'row': row,
                            'column': column,
                            'is_active': is_active,
                        },
                    )
                    space.space_type = space_type
                    space.row = row
                    space.column = column
                    space.is_active = is_active
                    space.save()
                    spaces[(parking_name, number)] = space

        return spaces

    def create_tariffs(self, parkings, space_types):
        prices = {
            'Стандартне': Decimal('40.00'),
            'Електромобіль': Decimal('55.00'),
            'Для людей з інвалідністю': Decimal('25.00'),
        }

        tariffs = {}

        for parking in parkings.values():
            for type_name, space_type in space_types.items():
                tariff, _ = Tariff.objects.get_or_create(
                    parking_lot=parking,
                    space_type=space_type,
                    defaults={
                        'price_per_hour': prices[type_name],
                        'is_active': True,
                    },
                )
                tariff.price_per_hour = prices[type_name]
                tariff.is_active = True
                tariff.save()
                tariffs[(parking.name, type_name)] = tariff

        return tariffs

    def create_vehicles(self, user):
        data = [
            {
                'license_plate': 'AA1234BB',
                'brand': 'Toyota',
                'model': 'Corolla',
                'year': 2020,
                'vehicle_type': Vehicle.TYPE_CAR,
                'color': Vehicle.COLOR_BLUE,
            },
            {
                'license_plate': 'KA7777EE',
                'brand': 'Nissan',
                'model': 'Leaf',
                'year': 2021,
                'vehicle_type': Vehicle.TYPE_ELECTRIC,
                'color': Vehicle.COLOR_WHITE,
            },
        ]

        vehicles = {}

        for item in data:
            vehicle, _ = Vehicle.objects.get_or_create(
                user=user,
                license_plate=item['license_plate'],
                defaults=item,
            )

            for field, value in item.items():
                setattr(vehicle, field, value)

            vehicle.user = user
            vehicle.is_active = True
            vehicle.save()
            vehicles[vehicle.license_plate] = vehicle

        return vehicles

    def create_reservations(self, user, vehicles, spaces, tariffs):
        now = timezone.now()

        data = [
            {
                'token': 'demo-active-reservation',
                'parking_space': spaces[('Demo Parking Center', 'A1')],
                'vehicle': vehicles['AA1234BB'],
                'tariff': tariffs[('Demo Parking Center', 'Стандартне')],
                'car_number': 'AA1234BB',
                'start_time': now - timezone.timedelta(minutes=30),
                'end_time': now + timezone.timedelta(hours=2),
                'status': Reservation.STATUS_ACTIVE,
                'is_paid': True,
                'overtime_fee': Decimal('0.00'),
                'final_price': None,
            },
            {
                'token': 'demo-checked-in-reservation',
                'parking_space': spaces[('Demo Parking Center', 'A2')],
                'vehicle': vehicles['KA7777EE'],
                'tariff': tariffs[('Demo Parking Center', 'Стандартне')],
                'car_number': 'KA7777EE',
                'start_time': now - timezone.timedelta(hours=4),
                'end_time': now - timezone.timedelta(hours=1),
                'status': Reservation.STATUS_CHECKED_IN,
                'check_in_time': now - timezone.timedelta(hours=4),
                'is_paid': True,
                'overtime_fee': Decimal('0.00'),
                'final_price': None,
            },
            {
                'token': 'demo-completed-reservation',
                'parking_space': spaces[('Demo Parking Center', 'B1')],
                'vehicle': vehicles['AA1234BB'],
                'tariff': tariffs[('Demo Parking Center', 'Стандартне')],
                'car_number': 'AA1234BB',
                'start_time': now - timezone.timedelta(days=2, hours=3),
                'end_time': now - timezone.timedelta(days=2, hours=1),
                'status': Reservation.STATUS_COMPLETED,
                'check_in_time': now - timezone.timedelta(days=2, hours=3),
                'check_out_time': now - timezone.timedelta(days=2),
                'is_paid': True,
                'overtime_fee': Decimal('40.00'),
                'overtime_is_paid': False,
                'final_price': Decimal('120.00'),
            },
            {
                'token': 'demo-cancelled-reservation',
                'parking_space': spaces[('Demo Parking Campus', 'A1')],
                'vehicle': vehicles['AA1234BB'],
                'tariff': tariffs[('Demo Parking Campus', 'Стандартне')],
                'car_number': 'AA1234BB',
                'start_time': now + timezone.timedelta(days=1),
                'end_time': now + timezone.timedelta(days=1, hours=2),
                'status': Reservation.STATUS_CANCELLED,
                'is_paid': False,
                'overtime_fee': Decimal('0.00'),
                'final_price': None,
            },
        ]

        for item in data:
            access_token = uuid.uuid5(uuid.NAMESPACE_DNS, item.pop('token'))
            reservation, _ = Reservation.objects.get_or_create(
                access_token=access_token,
                defaults={
                    'user': user,
                    **item,
                },
            )

            for field, value in item.items():
                setattr(reservation, field, value)

            reservation.user = user
            reservation.save()
