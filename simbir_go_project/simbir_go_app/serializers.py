from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, OutstandingToken
from django.core.validators import MinValueValidator, MaxValueValidator
from .models import *

class SimbirGoUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimbirGoUser
        fields = '__all__'

class SimbirGoUserSignInSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=30)
    password = serializers.CharField(max_length=128)

class SimbirGoUserSignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimbirGoUser
        fields = ['username', 'password']

class TransportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transport
        fields = '__all__'

class TransportDetailPutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transport
        fields = ['can_be_rented', 'model', 'color', 'identifier', 'description', 'latitude', 'longitude', 'minute_price', 'day_price']

class TransportPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transport
        fields = ['can_be_rented','transport_type', 'model', 'color', 'identifier', 'description', 'latitude', 'longitude', 'minute_price', 'day_price']


class RentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rent
        fields = '__all__'

class TransportRentSerializer(serializers.Serializer):
    lat = serializers.FloatField(
        validators=[
            MinValueValidator(limit_value=-90.0),
            MaxValueValidator(limit_value=90.0)
        ])
    long = serializers.FloatField(
        validators=[
            MinValueValidator(limit_value=-180.0),
            MaxValueValidator(limit_value=180.0)
        ]
    )
    radius = serializers.FloatField()
    transport_type = serializers.CharField(max_length=10)

class TransportRentEndSerializer(serializers.Serializer):
    lat = serializers.FloatField(
        validators=[
            MinValueValidator(limit_value=-90.0),
            MaxValueValidator(limit_value=90.0)
        ]
    )
    long = serializers.FloatField(
        validators=[
            MinValueValidator(limit_value=-180.0),
            MaxValueValidator(limit_value=180.0)
        ]
    )

class AdminAccountViewSerializer(serializers.Serializer):
    start = serializers.IntegerField(validators=[MinValueValidator(limit_value=0)])
    count = serializers.IntegerField(validators=[MinValueValidator(limit_value=0)])

class AdminTransportViewSerializer(serializers.Serializer):
    start = serializers.IntegerField()
    count = serializers.IntegerField()
    transport_type = serializers.ChoiceField(choices=['Car', 'Bike', 'Scooter', 'All'])
