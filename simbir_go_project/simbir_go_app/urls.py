from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

urlpatterns = [

    ### Account ###

    path('api/Account/Me', AccountMeView.as_view(), name='account-me'),
    path('api/Account/SignIn', AccountSignInView.as_view(), name='account-signin'),
    path('api/Account/SignIn/Refresh', TokenRefreshView.as_view(),
         name='account-signin-refresh'),
    path('api/Account/SignUp', AccountSignUpView.as_view(), name='account-signup'),
    path('api/Account/SignOut', AccountSignOutView.as_view(), name='account-signout'),
    path('api/Account/Update', AccountUpdateView.as_view(), name='account-update'),

    ### Transport ###

    path('api/Transport/<int:transportId>',
         TransportDetailView.as_view(), name='transport-detail'),
    path('api/Transport', TransportView.as_view(), name='transport-list'),

    ### Rent ###

    path('api/Rent/Transport', RentTransportView.as_view(), name='rent-transport'),
    path('api/Rent/<int:rentId>', RentDetailView.as_view(), name='rent-detail'),
    path('api/Rent/MyHistory', RentMyHistoryView.as_view(), name='rent-my-history'),
    path('api/Rent/TransportHistory/<int:transportId>',
         RentTransportHistoryView.as_view(), name='rent-transport-history'),
    path('api/Rent/New/<int:transportId>',
         RentNewView.as_view(), name='rent-new'),
    path('api/Rent/End/<int:rentId>', RentEndView.as_view(), name='rent-end'),

    ### Payment ###

    path('api/Payment/Hesoyam/<int:accountId>',
         PaymentHesoyamView.as_view(), name='payment-hesoyam'),

    ### Admin-Account ###

    path('api/Admin/Account', AdminAccountView.as_view(), name='admin-account'),
    path('api/Admin/Account/<int:userId>',
         AdminAccountDetailView.as_view(), name='admin-account-detail'),

    ### Admin-Transport ###

    path('api/Admin/Transport', AdminTransportView.as_view(), name='admin-account'),
    path('api/Admin/Transport/<int:transportId>',
         AdminTransportDetailView.as_view(), name='admin-account-detail'),

    ### Admin-Rent ###

    path('api/Admin/Rent/<int:rentId>', AdminRentDetailView.as_view(),
         name='admin-rent-detail'),
    path('api/Admin/UserHistory/<int:userId>',
         AdminRentUserHistoryView.as_view(), name='admin-rent-user-history'),
    path('api/Admin/TransportHistory/<int:transportId>',
         AdminRentTransportHistoryView.as_view(), name='admin-rent-transport-history'),
    path('api/Admin/Rent', AdminRentView.as_view(), name='admin-rent-view'),
    path('api/Admin/Rent/End<int:rentId>',
         AdminRentEndView.as_view(), name='admib-rent-end-view'),

]