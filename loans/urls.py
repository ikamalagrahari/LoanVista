from django.urls import path
from django.shortcuts import render
from .views import RegisterCustomer, CheckEligibility, CreateLoan, ViewLoan, ViewLoans, ViewLoanForm, ViewLoansForm, UploadData, TrackLoans

def api_home(request):
    return render(request, 'api.html')

urlpatterns = [
    path('', api_home, name='api_home'),
    path('register', RegisterCustomer.as_view(), name='register'),
    path('check-eligibility', CheckEligibility.as_view(), name='check-eligibility'),
    path('create-loan', CreateLoan.as_view(), name='create-loan'),
    path('view-loan', ViewLoanForm.as_view(), name='view-loan-form'),
    path('view-loan/<int:loan_id>', ViewLoan.as_view(), name='view-loan'),
    path('view-loans', ViewLoansForm.as_view(), name='view-loans-form'),
    path('view-loans/<int:customer_id>', ViewLoans.as_view(), name='view-loans'),
    path('track-loans', TrackLoans.as_view(), name='track-loans'),
    path('upload-data', UploadData.as_view(), name='upload-data'),
]