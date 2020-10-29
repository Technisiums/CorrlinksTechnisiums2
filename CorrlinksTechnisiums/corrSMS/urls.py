from django.urls import path, include
from .views import GetAccounts, PostCorrlinksToSMS, ListenFormBandwith, SMSToCorrlinksView, setSMStoCorrlinksStatus,addPhoneBook,ABC,setSystemtoCorrlinksStatus,SystemToCorrlinksPendingsView, RUN_AT_8PM, ImageUpload

urlpatterns = [
    # path('acc/', sample),
    path('getAcc/', GetAccounts.as_view()),
    path('sendSMS/', PostCorrlinksToSMS.as_view()),
    path('getPendingSMS/', SMSToCorrlinksView.as_view()),
    path('setSMSToCorrlinksStatus/', setSMStoCorrlinksStatus.as_view()),
    path('addPhoneBook/', addPhoneBook.as_view()),
    # path('abc/', ImageUpload.as_view()),
    path('listenFromBandwidth/', ListenFormBandwith.as_view()),


    path('runat8pm/', RUN_AT_8PM.as_view()),  # relative to corrlinks
    path('setSystemToCorrlinksStatus/', setSystemtoCorrlinksStatus.as_view()),  # relative to corrlinks
    path('getPendingSystemSMS/', SystemToCorrlinksPendingsView.as_view()),  # relative to corrlinks
]
