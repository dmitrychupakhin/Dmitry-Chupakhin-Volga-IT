from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class SimbirGoUserManager(BaseUserManager):
    def create_user(self, username, password, balance=0, **extra_fields):
        user = self.model(username=username, balance=balance, **extra_fields)
        user.password = password
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, balance=0, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, balance, **extra_fields)

class SimbirGoUser(AbstractBaseUser):
    username = models.CharField(max_length=30, unique=True)
    password = models.CharField(max_length=128)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_superuser = models.BooleanField(default=False)
    last_login = None
    objects = SimbirGoUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username

class Transport(models.Model):
    can_be_rented = models.BooleanField(default=True)
    transport_type = models.CharField(max_length=10, choices=[(
        'Car', 'Car'), ('Bike', 'Bike'), ('Scooter', 'Scooter')])
    model = models.CharField(max_length=255)
    color = models.CharField(max_length=50)
    identifier = models.CharField(max_length=20, unique=True)
    description = models.TextField(null=True, blank=True)
    latitude = models.DecimalField(max_digits=12, decimal_places=9, validators=[
            MaxValueValidator(90),
            MinValueValidator(-90),
        ])
    longitude = models.DecimalField(max_digits=12, decimal_places=9, validators=[
            MaxValueValidator(180),
            MinValueValidator(-180),
        ])
    minute_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, default=-1, validators=[
            MinValueValidator(-1),
        ])
    day_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, default=-1, validators=[
            MinValueValidator(-1),
        ])
    owner = models.ForeignKey(SimbirGoUser, on_delete=models.CASCADE)

class Rent(models.Model):
    # Пользователь, который арендует
    renter = models.ForeignKey(
        SimbirGoUser, on_delete=models.CASCADE)
    transport = models.ForeignKey(
        Transport, on_delete=models.SET_NULL, null=True)  # Арендуемый транспорт
    rent_type = models.CharField(max_length=10, choices=[
                                 ('Minutes', 'Minutes'), ('Days', 'Days')])
    price_of_unit = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, default=-1)
    start_time = models.DateTimeField(blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    total_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)