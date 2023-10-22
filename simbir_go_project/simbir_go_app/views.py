from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from drf_yasg.utils import swagger_auto_schema
from decimal import Decimal
from geopy.distance import geodesic
from .models import *
from .serializers import *
from .simbir_go_auth import *
from .permissions import *
from drf_yasg import openapi

### Account ###

class AccountMeView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="""
        Описание: Получение данных о текущем аккаунте
        Ограничения: Только авторизованные пользователи
        """,
        responses={status.HTTP_200_OK: openapi.Response('Success', SimbirGoUserSerializer)},
    )
    def get(self, request):
        serializer = SimbirGoUserSerializer(
            SimbirGoUser.objects.get(id=request.user.id))
        return Response(serializer.data, status=status.HTTP_200_OK)

class AccountSignInView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="""
        Описание: Получение нового jwt access и refresh токена пользователя
        Ограничения: Нет
        Дополнительная информация: 
        
        Чтобы авторизоваться с использованием JWT access токена, необходимо передать 'JWT {accesstoken}' в заголовок Authorization. Также это требуется для Swagger: 'JWT {accesstoken}'.

        Время жизни access токена ограничено. Он может перестать быть валидным, если истечет его срок действия. Для его обновления необходимо передать refresh токен на api/SignIn/Refresh. Если refresh токен также перестанет быть валидным (из-за истечения срока действия, повторной авторизации или деавторизации), потребуется повторно выполнить процедуру авторизации.
        """,
        request_body=SimbirGoUserSignInSerializer,
        responses={status.HTTP_200_OK: TokenRefreshSerializer},
    )
    def post(self, request):
        serializer = SimbirGoUserSignInSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = simbir_go_authenticate(username=username, password=password)
            if user is not None:
                try:
                    token = OutstandingToken.objects.filter(
                        user_id=user.id).latest('created_at')
                    RefreshToken(token.token).blacklist()
                except:
                    pass
                refresh = RefreshToken.for_user(user)
                access = refresh.access_token
                return Response({"refresh": str(refresh), 'access': str(access)}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Неправильные учетные данные"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AccountSignUpView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="""Описание: Регистрация нового аккаунта
        Ограничения: Нельзя создать пользователя с существующим username
        """,
        request_body=SimbirGoUserSignUpSerializer,
        responses={status.HTTP_201_CREATED: openapi.Response('Success', SimbirGoUserSerializer)},
    )
    def post(self, request):
        serializer = SimbirGoUserSignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(SimbirGoUserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class AccountSignOutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="""Описание: Выход из аккаунта
        Ограничения: Только авторизованные пользователи
        """,
        responses={status.HTTP_201_CREATED: '"message": "Вы успешно вышли из аккаунта"'},
    )
    def post(self, request):
        user = request.user
        try:
            token = OutstandingToken.objects.filter(
                user_id=user.id).latest('created_at')
            RefreshToken(token.token).blacklist()
        except:
            pass

        return Response({"message": "Вы успешно вышли из аккаунта"}, status=status.HTTP_200_OK)

class AccountUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="""Описание: Обновление своего аккаунта
        Ограничения: Только авторизованные пользователи, нельзя использовать уже используемые в системе username
        """,
        request_body=SimbirGoUserSignUpSerializer,
        responses={status.HTTP_200_OK: openapi.Response('Success', SimbirGoUserSerializer)},
    )
    def put(self, request):

        user_instance = SimbirGoUser.objects.get(id=request.user.id)
        serializer = SimbirGoUserSignUpSerializer(user_instance, data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(SimbirGoUserSerializer(user).data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

### Account-Admin ###

class AdminAccountView(APIView):
    permission_classes = [IsSuperUser]
    @swagger_auto_schema(
        operation_description="""Описание: Получение списка всех аккаунтов
        Ограничения: Только администраторы
        """,
        manual_parameters=[
            openapi.Parameter('start', openapi.IN_QUERY, description="Начало выборки", type=openapi.TYPE_NUMBER),
            openapi.Parameter('count', openapi.IN_QUERY, description="Размер выборки", type=openapi.TYPE_NUMBER),
        ],
        responses={status.HTTP_200_OK: openapi.Response('Success', SimbirGoUserSerializer(many=True))}
    )
    def get(self, request):
        serializer = AdminAccountViewSerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        start = serializer.validated_data['start']
        count = serializer.validated_data['count']

        all_accounts = SimbirGoUser.objects.all()

        available_accounts = all_accounts[int(start):int(start) + int(count)]

        users_serializer = SimbirGoUserSerializer(available_accounts, many=True)

        return Response(users_serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="""Описание: Создание администратором нового аккаунта
        Ограничения: Только администраторы, нельзя создать аккаунт с уже существующим в системе username
        """,
        request_body=SimbirGoUserSerializer,
        responses={status.HTTP_201_CREATED: openapi.Response('Success', SimbirGoUserSerializer)},
    )
    def post(self, request):

        serializer = SimbirGoUserSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class AdminAccountDetailView(APIView):
    permission_classes = [IsSuperUser]
    @swagger_auto_schema(
        operation_description="""Описание: Получение информации об аккаунте по id
        Ограничения: Только администраторы
        """,
        responses={status.HTTP_200_OK: openapi.Response('Success', SimbirGoUserSerializer)}
    )
    def get(self, request, userId):
        try:
            user = SimbirGoUser.objects.get(id=userId)
            serializer = SimbirGoUserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except SimbirGoUser.DoesNotExist:
            return Response({"message": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="""Описание: Изменение администратором аккаунта по id
        Ограничения: Только администраторы, нельзя изменять username на уже существующий в системе""",
        request_body=SimbirGoUserSerializer,
        responses={status.HTTP_201_CREATED: openapi.Response('Success', SimbirGoUserSerializer)},
    )
    def put(self, request, userId):
        user_instance = SimbirGoUser.objects.get(id=userId)
        serializer = SimbirGoUserSerializer(user_instance, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="""Описание: Удаление аккаунта по id
        Ограничения: Только администраторы
        """,
        responses={status.HTTP_200_OK: "'message':'Пользователь успешно удален'"}
    )
    def delete(self, request, userId):
        try:
            user = SimbirGoUser.objects.get(id=userId)
            user.delete()
            return Response({"message": "Пользователь успешно удален"}, status=status.HTTP_200_OK)
        except SimbirGoUser.DoesNotExist:
            return Response({"message": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

### Payment ###

class PaymentHesoyamView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="""Описание: Добавляет на баланс аккаунта с id={accountId} 250 000 денежных единиц
        Ограничения: Администратор может добавить баланс всем, обычный пользователь только себе
        """,
        responses={status.HTTP_200_OK: '"message": "Баланс успешно пополнен"'}
    )
    def post(self, request, accountId):

        try:
            user = SimbirGoUser.objects.get(id=accountId)
        except:
            return Response({"error": "Пользователь с данным Id не найден"}, status=status.HTTP_400_BAD_REQUEST)

        request_user = SimbirGoUser.objects.get(id=request.user.id)

        if request_user == user:
            user.balance += 250000
            user.save()
        elif request_user != user and request_user.is_superuser == True:
            user.balance += 250000
            user.save()
        else:
            return Response({"error": "Только superuser может пополнять баланс других пользователей"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Баланс успешно пополнен"}, status=status.HTTP_200_OK)

### Transport ###

class TransportDetailView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @swagger_auto_schema(
        operation_description="""Описание: Получение информации о транспорте по id
        Ограничения: Нет
        """,
        responses={status.HTTP_200_OK: openapi.Response('Success', TransportSerializer)},
    )
    def get(self, request, transportId):
        try:
            transport = Transport.objects.get(id=transportId)
            serializer = TransportSerializer(transport)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Transport.DoesNotExist:
            return Response({"error": "Транспорт не найден"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(   
        operation_description="""Описание: Изменение транспорта оп id
            Ограничения: Только владелец этого транспорта
            """,
        request_body=TransportDetailPutSerializer,
        responses={status.HTTP_201_CREATED: openapi.Response('Success', TransportSerializer)},
    )
    def put(self, request, transportId):
        try:
            transport = Transport.objects.get(id=transportId)
            if request.user == transport.owner:
                if transport.latitude == -1 or transport.longitude == -1:
                    return Response({"error": "Транспорт находится в поездке"}, status=status.HTTP_400_BAD_REQUEST)
                serializer = TransportDetailPutSerializer(transport, data=request.data)
                if serializer.is_valid():
                    transport = serializer.save()
                    if transport.minute_price == -1 and transport.day_price == -1:
                        transport.can_be_rented = False
                    transport.save()
                    return Response(TransportSerializer(transport).data, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": "Вы можете редактировать только свой транспорт"}, status=status.HTTP_400_BAD_REQUEST)
        except Transport.DoesNotExist:
            return Response({"message": "Транспорт не найден"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="""Описание: Удаление транспорта по id
        Ограничения: Только владелец этого транспорта""",
        responses={status.HTTP_200_OK: '"message": "Транспорт успешно удален"'},
    )
    def delete(self, request, transportId):
        try:
            transport = Transport.objects.get(id=transportId)
            if request.user == transport.owner:
                if transport.longitude != -1 and transport.latitude != -1:
                    transport.delete()
                    return Response({"message": "Транспорт успешно удален"}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Транспорт находится в поездке"}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({"error": "Вы можете редактировать только свой транспорт"}, status=status.HTTP_400_BAD_REQUEST)
        except Transport.DoesNotExist:
            return Response({"message": "Транспорт не найден"}, status=status.HTTP_404_NOT_FOUND)

class TransportView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(   
        operation_description="""Описание: Добавление нового транспорта
            Ограничения: Только авторизованные пользователи
            Дополнительная информация: Если day_price и minute_price будет None, can_be_rented будет установлен на False
            """,
        request_body=TransportPostSerializer,
        responses={status.HTTP_201_CREATED: openapi.Response('Success', TransportSerializer)},
    )
    def post(self, request):
        serializer = TransportPostSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            data['owner'] = request.user.id
            transport_serializer = TransportSerializer(data=data)
            if transport_serializer.is_valid():
                transport = transport_serializer.save()
                if transport.minute_price == -1 and transport.day_price == -1:
                    transport.can_be_rented = False
                transport.save()
                return Response(TransportSerializer(transport).data, status=status.HTTP_201_CREATED)
            else:
                return Response(transport_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

### Admin-Transport ###

class AdminTransportView(APIView):
    permission_classes = [IsSuperUser]
    @swagger_auto_schema(
        operation_description="""Описание: Получение списка всех транспортных средств
        Ограничения: Только администраторы
        """,
        manual_parameters=[
            openapi.Parameter('start', openapi.IN_QUERY, description="Начало выборки", type=openapi.TYPE_NUMBER),
            openapi.Parameter('count', openapi.IN_QUERY, description="Размер выборки", type=openapi.TYPE_NUMBER),
            openapi.Parameter('transport_type', openapi.IN_QUERY, description="Тип транспорта[Car, Bike, Scooter, All]", type=openapi.TYPE_STRING),
        ],
        responses={status.HTTP_200_OK: openapi.Response('Success', SimbirGoUserSerializer(many=True))}
    )
    def get(self, request):

        serializer = AdminTransportViewSerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        transport_type = serializer.validated_data['transport_type']
        start = serializer.validated_data['start']
        count = serializer.validated_data['count']

        all_transport = []

        if transport_type != 'All':
            all_transport = Transport.objects.filter(transport_type=transport_type)
        else:
            all_transport = Transport.objects.all()

        available_transport = all_transport[int(start):int(start) + int(count)]

        transport_serializer = TransportSerializer(available_transport, many=True)

        return Response(transport_serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="""Описание: Создание нового транспортного средства
        Ограничения: Только администраторы""",
        request_body = TransportSerializer,
        responses={status.HTTP_200_OK: openapi.Response('Success', TransportSerializer())}
    )
    def post(self, request):
        serializer = TransportSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

class AdminTransportDetailView(APIView):
    permission_classes = [IsSuperUser]

    @swagger_auto_schema(
        operation_description="""Описание: Получение информации о транспортном средстве по id
        Ограничения: Только администраторы""",
        
        responses={status.HTTP_200_OK: openapi.Response('Success', TransportSerializer())}
    )
    def get(self, request, transportId):
        try:
            serializer = TransportSerializer(Transport.objects.get(id=transportId))
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Transport.DoesNotExist:
            return Response("error: Транспорт не найден", status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="""Описание: Изменение транспортного средства
        Ограничения: Только администраторы""",
        request_body = TransportSerializer,
        responses={status.HTTP_200_OK: openapi.Response('Success', TransportSerializer())}
    )
    def put(self, request, transportId):
        try:
            transport = Transport.objects.get(id=transportId)
        except Transport.DoesNotExist:
            return Response("error: Транспорт не найден", status=status.HTTP_404_NOT_FOUND)
        serializer = TransportSerializer(transport, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="""Описание: Удаление транспорта по id
        Ограничения: Только администраторы""",
        
        responses={status.HTTP_200_OK: '"message": "Транспорт удален успешно"'}
    )
    def delete(self, request, transportId):
        try:
            transport = Transport.objects.get(id=transportId)
            if transport.longitude != -1 and transport.latitude != -1:
                transport.delete()
            else:
                return Response({"message": "Транспорт находится в поездке"}, status=status.HTTP_204_NO_CONTENT)
            return Response({"message": "Транспорт удален успешно"}, status=status.HTTP_200_OK)
        except:
            return Response({"error": "Транспорт не найден"}, status=status.HTTP_404_NOT_FOUND)

### Rent ###

class RentTransportView(APIView):

    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_description="""Описание: Получение транспорта доступного для аренды по параметрам
        Ограничения: Нет
        """,
        manual_parameters=[
            openapi.Parameter('lat', openapi.IN_QUERY, description="Географическая широта центра круга поиска транспорта", type=openapi.TYPE_NUMBER),
            openapi.Parameter('long', openapi.IN_QUERY, description="Географическая долгота центра круга поиска транспорта", type=openapi.TYPE_NUMBER),
            openapi.Parameter('radius', openapi.IN_QUERY, description="Радиус круга поиска транспорта в метрах", type=openapi.TYPE_NUMBER),
            openapi.Parameter('transport_type', openapi.IN_QUERY, description="Тип транспорта [Car, Bike, Scooter, All]", type=openapi.TYPE_STRING),
        ],
        responses={status.HTTP_200_OK: openapi.Response('Success', TransportSerializer(many=True))}
    )
    def get(self, request):

        serializer = TransportRentSerializer(data=request.query_params)

        if serializer.is_valid():
            user_location = (
                serializer.validated_data['lat'], serializer.validated_data['long'])

            all_transport = Transport.objects.filter(can_be_rented=True)

            if serializer.validated_data['transport_type'] != "All":
                all_transport = Transport.objects.filter(
                    transportType=serializer.validated_data['transport_type'])

            filtered_transport = [transport for transport in all_transport if geodesic(
                user_location, (transport.latitude, transport.longitude)).meters <= float(serializer.validated_data['radius'])]
            transport_serializer = TransportSerializer(
                filtered_transport, many=True)
            return Response(transport_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="""Описание: Получение информации об аренде по id
        Ограничения: Только арендатор и владелец транспорта
        """,
        responses={status.HTTP_200_OK: openapi.Response('Success', RentSerializer)},
    )
    def get(self, request, rentId):
        try:
            rent = Rent.objects.get(id=rentId)
            if request.user != rent.renter and request.user != rent.transport.owner:
                return Response({"error": ": Только арендатор и владелец транспорта имеет право на получение информации об аренде по id"}, status=status.HTTP_400_BAD_REQUEST)
            serializer = RentSerializer(rent)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Rent.DoesNotExist:
            return Response({"message": "Аренда не найдена"}, status=status.HTTP_404_NOT_FOUND)

class RentMyHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="""Описание: Получение истории аренд текущего аккаунта
        Ограничения: Только авторизованные пользователи""",
        responses={status.HTTP_200_OK: openapi.Response('Success', RentSerializer(many=True))},
    )
    def get(self, request):
        user = request.user
        rents = Rent.objects.filter(renter=user)
        serializer = RentSerializer(rents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RentTransportHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="""Описание: Получение истории аренд транспорта
        Ограничения: Только владелец этого транспорта""",
        responses={status.HTTP_200_OK: openapi.Response('Success', RentSerializer(many=True))},
    )
    def get(self, request, transportId):
        try:
            transport = Transport.objects.get(id=transportId)
            if(transport.owner != request.user):
                return Response({"error": ": Только владелец транспорта имеет право на получение информации об истории аренд транспорта"}, status=status.HTTP_400_BAD_REQUEST)
            rents = Rent.objects.filter(transport=transport)
            serializer = RentSerializer(rents, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Transport.DoesNotExist:
            return Response({"message": "Транспорт не найден"}, status=status.HTTP_404_NOT_FOUND)

class RentNewView(APIView):

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="""Описание: : Аренда транспорта в личное пользование
        Ограничения: Только авторизованные пользователи, нельзя брать в аренду собственный транспорт""",
        manual_parameters=[
            openapi.Parameter('rent_type', openapi.IN_QUERY, description="Тип аренды [Minutes, Days]", type=openapi.TYPE_STRING),
        ],
        responses={status.HTTP_200_OK: openapi.Response('Success', RentSerializer())}
    )
    def post(self, request, transportId):
        try:
            transport = Transport.objects.get(id=transportId)
        except Transport.DoesNotExist:
            return Response({'errors': "Транспорт не найден"}, status=status.HTTP_404_NOT_FOUND)

        if not transport.can_be_rented:
            return Response({'errors': "Нельзя арендовать данный транспорт"}, status=status.HTTP_400_BAD_REQUEST)

        if transport.owner == request.user:
            return Response({'errors': "Нельзя брать в аренду собственный транспорт"}, status=status.HTTP_400_BAD_REQUEST)

        rent_type = request.query_params.get('rent_type')

        if rent_type not in ["Minutes", "Days"]:
            return Response({'errors': "Неверный тип аренды"}, status=status.HTTP_400_BAD_REQUEST)

        price_of_unit = transport.minute_price if rent_type == "Minutes" else transport.day_price

        if price_of_unit < 0:
            return Response({'errors': f"Данный вид транспорта не поддерживает цену аренды за {rent_type.lower()}"}, status=status.HTTP_400_BAD_REQUEST)

        data = {
            'rent_type': rent_type,
            'renter': request.user.id,
            'transport': transport.id,
            'price_of_unit': price_of_unit,
            'start_time': timezone.now()
        }

        rent_serializer = RentSerializer(data=data)

        if rent_serializer.is_valid():
            rent_serializer.save()
            transport.can_be_rented = False
            transport.latitude = -1
            transport.longitude = -1
            transport.save()
            return Response({"message": "Аренда успешно создана"}, status=status.HTTP_201_CREATED)
        else:
            return Response({'errors': rent_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class RentEndView(APIView):

    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="""Описание: Завершение аренды транспорта по id аренды
        Ограничения: Только человек который создавал эту аренду""",
        manual_parameters=[
            openapi.Parameter('lat', openapi.IN_QUERY, description="Географическая широта местонахождения транспорта", type=openapi.TYPE_NUMBER),
            openapi.Parameter('long', openapi.IN_QUERY, description="Географическая долгота местонахождения транспорта", type=openapi.TYPE_NUMBER),
        ],
        responses={status.HTTP_200_OK: openapi.Response('Success', RentSerializer())}
    )
    def post(self, request, rentId):
        serializer = TransportRentEndSerializer(data=request.query_params)
    
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        lat = serializer.validated_data['lat']
        long = serializer.validated_data['long']

        try:
            rent = Rent.objects.get(id=rentId)
        except Rent.DoesNotExist:
            return Response({"error": "Аренды с таким id не существует"}, status=status.HTTP_400_BAD_REQUEST)

        if request.user != rent.renter:
            return Response({"error": "Завершить аренду может только человек, который создал эту аренду"}, status=status.HTTP_400_BAD_REQUEST)

        if rent.end_time is not None:
            return Response({"error": "Аренда уже завершена"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transport = rent.transport
            transport.latitude = Decimal(lat)
            transport.longitude = Decimal(long)
            transport.can_be_rented = True
            transport.save()
        except:
            return Response({"error": "Неверные геоданные"}, status=status.HTTP_400_BAD_REQUEST)

        rent.end_time = timezone.now()
        time_difference = rent.end_time - rent.start_time

        if rent.rent_type == "Minutes":
            total_minutes = (time_difference.seconds + 59) // 60
            rent.total_price = rent.transport.minute_price * total_minutes
        elif rent.rent_type == "Days":
            total_days = time_difference.days + 1 if time_difference.seconds > 0 else time_difference.days
            rent.total_price = rent.transport.day_price * total_days
        rent.save()

        rent_serializer = RentSerializer(rent)
        request.user.balance -= rent.total_price
        request.user.save()

        return Response(rent_serializer.data, status=status.HTTP_200_OK)
  
### Admin-Rent ###

class AdminRentDetailView(APIView):
    permission_classes = [IsSuperUser]

    @swagger_auto_schema(
        operation_description="""Описание: Получение информации по аренде по id
        Ограничения: Только администраторы""",
        
        responses={status.HTTP_200_OK: openapi.Response('Success', RentSerializer())}
    )
    def get(self, request, rentId):
        try:
            rent = Rent.objects.get(id=rentId)
            serializer = RentSerializer(rent)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Rent.DoesNotExist:
            return Response({"error": "Аренда не найдена"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="""Описание: Изменение записи об аренде по id
        Ограничения: Только администраторы""",
        
        request_body = RentSerializer,

        responses={status.HTTP_200_OK: openapi.Response('Success', RentSerializer())}
    )
    def put(self, request, rentId):
        try:
            rent = Rent.objects.get(id=rentId)
            serializer = RentSerializer(rent, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except:
            return Response({"error": "Аренда не найдена"}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="""Описание: Удаление информации об аренде по id
        Ограничения: Только администраторы""",
        
        responses={status.HTTP_200_OK: '"message": "Аренда успешно удалена"'}
    )
    def delete(self, request, rentId):
        try:
            rent = Rent.objects.get(id=rentId)
            rent.delete()
            return Response({"message": "Аренда успешно удалена"})
        except Rent.DoesNotExist:
            return Response({'error': 'Аренда не найдена'})

class AdminRentUserHistoryView(APIView):
    permission_classes = [IsSuperUser]

    @swagger_auto_schema(
        operation_description="""Описание: Получение истории аренд пользователя с id={userId}
        Ограничения: Только администраторы""",
        
        responses={status.HTTP_200_OK: openapi.Response('Success', RentSerializer(many=True))}
    )
    def get(self, request, userId):
        rents = Rent.objects.filter(renter=userId)
        serializer = RentSerializer(rents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AdminRentTransportHistoryView(APIView):
    permission_classes = [IsSuperUser]

    @swagger_auto_schema(
        operation_description="""Описание: Получение истории аренд транспорта с id={transportId}
        Ограничения: Только администраторы""",
        
        responses={status.HTTP_200_OK: openapi.Response('Success', RentSerializer(many=True))}
    )
    def get(self, request, transportId):
        rents = Rent.objects.filter(transport=transportId)
        serializer = RentSerializer(rents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class AdminRentView(APIView):
    permission_classes = [IsSuperUser]

    @swagger_auto_schema(
        operation_description="""Описание: Создание новой аренды
        Ограничения: Только администраторы""",
        
        request_body = RentSerializer,

        responses={status.HTTP_200_OK: openapi.Response('Success', RentSerializer())}
    )
    def post(self, request):
        serializer = RentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminRentEndView(APIView):
    permission_classes = [IsSuperUser]

    @swagger_auto_schema(
        operation_description="""Описание: Завершение аренды транспорта по id аренды
        Ограничения: Только администраторы""",
        manual_parameters=[
            openapi.Parameter('lat', openapi.IN_QUERY, description="Географическая широта местонахождения транспорта", type=openapi.TYPE_NUMBER),
            openapi.Parameter('long', openapi.IN_QUERY, description="Географическая долгота местонахождения транспорта", type=openapi.TYPE_NUMBER),
        ],
        responses={status.HTTP_200_OK: openapi.Response('Success', RentSerializer())}
    )
    def post(self, request, rentId):
        serializer = TransportRentEndSerializer(data=request.query_params)
    
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        lat = serializer.validated_data['lat']
        long = serializer.validated_data['long']

        try:
            rent = Rent.objects.get(id=rentId)
        except Rent.DoesNotExist:
            return Response({"error": "Аренды с таким id не существует"}, status=status.HTTP_400_BAD_REQUEST)

        if rent.end_time is not None:
            return Response({"error": "Аренда уже завершена"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            transport = rent.transport
            transport.latitude = Decimal(lat)
            transport.longitude = Decimal(long)
            transport.can_be_rented = True
            transport.save()
        except:
            return Response({"error": "Неверные геоданные"}, status=status.HTTP_400_BAD_REQUEST)

        rent.end_time = timezone.now()
        time_difference = rent.end_time - rent.start_time

        if rent.rent_type == "Minutes":
            total_minutes = (time_difference.seconds + 59) // 60
            rent.total_price = rent.transport.minute_price * total_minutes
        elif rent.rent_type == "Days":
            total_days = time_difference.days + 1 if time_difference.seconds > 0 else time_difference.days
            rent.total_price = rent.transport.day_price * total_days

        rent.save()

        rent_serializer = RentSerializer(rent)
        request.user.balance -= rent.total_price
        request.user.save()

        return Response(rent_serializer.data, status=status.HTTP_200_OK)

