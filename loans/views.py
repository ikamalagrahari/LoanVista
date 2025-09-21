from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from django.utils import timezone
from django.shortcuts import render
from .models import Customer, Loan
from .serializers import CustomerSerializer, LoanSerializer, LoanListSerializer
import math
import openpyxl
import csv
import io
import decimal
import datetime


def calculate_credit_score(customer):
    loans = Loan.objects.filter(customer=customer)
    if not loans.exists():
        return 100

    current_loans = loans.filter(emis_paid_on_time__lt=models.F('tenure'))
    current_loan_sum = current_loans.aggregate(sum=models.Sum('loan_amount'))['sum'] or 0
    if current_loan_sum > customer.approved_limit:
        return 0

    current_emis_sum = current_loans.aggregate(sum=models.Sum('monthly_repayment'))['sum'] or 0
    if current_emis_sum > decimal.Decimal('0.5') * customer.monthly_salary:
        return 0

    total_emis = sum(l.tenure for l in loans)
    paid_on_time = sum(l.emis_paid_on_time for l in loans)
    paid_ratio = paid_on_time / total_emis if total_emis > 0 else 1

    no_loans = loans.count()
    current_year = timezone.now().year
    current_year_loans = loans.filter(start_date__year=current_year).count()
    volume = loans.aggregate(sum=models.Sum('loan_amount'))['sum'] or 0

    score = min(100, (paid_ratio * 40) + min(no_loans * 5, 20) + min(current_year_loans * 10, 20) + min(volume / 100000, 20))
    return int(score)


def calculate_emi(loan_amount, interest_rate, tenure):
    if interest_rate == 0:
        return loan_amount / tenure
    r = interest_rate / 12 / 100
    emi = (loan_amount * r * (1 + r) ** tenure) / ((1 + r) ** tenure - 1)
    return emi


class RegisterCustomer(APIView):
    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        age = request.data.get('age')
        monthly_income = request.data.get('monthly_income')
        phone_number = request.data.get('phone_number')

        if int(age) < 18:
            return Response({'error': 'Age must be at least 18'}, status=status.HTTP_400_BAD_REQUEST)

        approved_limit = round(36 * monthly_income / 100000) * 100000

        customer = Customer.objects.create(
            first_name=first_name,
            last_name=last_name,
            age=age,
            monthly_salary=monthly_income,
            approved_limit=approved_limit,
            phone_number=phone_number
        )
        customer.customer_id = customer.id
        customer.save()

        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CheckEligibility(APIView):
    def get(self, request):
        return render(request, 'check_eligibility.html')

    def post(self, request):
        customer_id = request.data.get('customer_id')
        loan_amount = request.data.get('loan_amount')
        interest_rate = request.data.get('interest_rate')
        tenure = request.data.get('tenure')

        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        score = calculate_credit_score(customer)
        approval = False
        corrected_interest_rate = interest_rate

        if score > 50:
            approval = True
        elif 30 < score <= 50:
            approval = True
            corrected_interest_rate = max(interest_rate, 12)
        elif 10 < score <= 30:
            approval = True
            corrected_interest_rate = max(interest_rate, 16)
        else:
            approval = False

        monthly_installment = calculate_emi(loan_amount, corrected_interest_rate, tenure)

        return Response({
            'customer_id': customer_id,
            'approval': approval,
            'interest_rate': interest_rate,
            'corrected_interest_rate': corrected_interest_rate,
            'tenure': tenure,
            'monthly_installment': monthly_installment
        })


class CreateLoan(APIView):
    def get(self, request):
        return render(request, 'create_loan.html')

    def post(self, request):
        customer_id = request.data.get('customer_id')
        loan_amount = request.data.get('loan_amount')
        interest_rate = request.data.get('interest_rate')
        tenure = request.data.get('tenure')

        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        score = calculate_credit_score(customer)
        approval = False
        corrected_interest_rate = interest_rate
        message = ''

        if score > 50:
            approval = True
        elif 30 < score <= 50:
            approval = True
            corrected_interest_rate = max(interest_rate, 12)
        elif 10 < score <= 30:
            approval = True
            corrected_interest_rate = max(interest_rate, 16)
        else:
            approval = False
            message = 'Credit score too low'

        if approval:
            monthly_installment = calculate_emi(loan_amount, corrected_interest_rate, tenure)
            loan = Loan.objects.create(
                customer=customer,
                loan_amount=loan_amount,
                tenure=tenure,
                interest_rate=corrected_interest_rate,
                monthly_repayment=monthly_installment,
                emis_paid_on_time=0,
                start_date=timezone.now().date(),
                end_date=timezone.now().date() + timezone.timedelta(days=tenure*30)
            )
            return Response({
                'loan_id': loan.loan_id,
                'customer_id': customer_id,
                'loan_approved': True,
                'monthly_installment': monthly_installment
            })
        else:
            return Response({
                'loan_id': None,
                'customer_id': customer_id,
                'loan_approved': False,
                'message': message
            })


class ViewLoanForm(APIView):
    def get(self, request):
        return render(request, 'view_loan.html')


class ViewLoan(APIView):
    def get(self, request, loan_id):
        try:
            loan = Loan.objects.get(loan_id=loan_id)
        except Loan.DoesNotExist:
            return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = LoanSerializer(loan)
        return Response(serializer.data)


class ViewLoans(APIView):
    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(customer_id=customer_id)
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        loans = Loan.objects.filter(customer=customer)
        data = []
        for loan in loans:
            repayments_left = loan.tenure - loan.emis_paid_on_time
            data.append({
                'loan_id': loan.loan_id,
                'loan_amount': loan.loan_amount,
                'interest_rate': loan.interest_rate,
                'monthly_installment': loan.monthly_repayment,
                'repayments_left': repayments_left
            })
        return Response(data)


class ViewLoansForm(APIView):
    def get(self, request):
        return render(request, 'view_loans.html')


class TrackLoans(APIView):
    def get(self, request):
        return render(request, 'track_loans.html')

    def post(self, request):
        loan_id = request.data.get('loan_id')
        customer_id = request.data.get('customer_id')

        if loan_id:
            # Track specific loan
            try:
                loan = Loan.objects.get(loan_id=loan_id)
                serializer = LoanSerializer(loan)
                return Response(serializer.data)
            except Loan.DoesNotExist:
                return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)
        elif customer_id:
            # Track all loans for customer
            try:
                customer = Customer.objects.get(customer_id=customer_id)
            except Customer.DoesNotExist:
                return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

            loans = Loan.objects.filter(customer=customer)
            data = []
            for loan in loans:
                repayments_left = loan.tenure - loan.emis_paid_on_time
                data.append({
                    'loan_id': loan.loan_id,
                    'loan_amount': loan.loan_amount,
                    'interest_rate': loan.interest_rate,
                    'monthly_installment': loan.monthly_repayment,
                    'repayments_left': repayments_left
                })
            return Response(data)
        else:
            return Response({'error': 'Please provide either loan_id or customer_id'}, status=status.HTTP_400_BAD_REQUEST)


class UploadData(APIView):
    def get(self, request):
        return render(request, 'upload_data.html')

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

        file_name = file.name.lower()
        try:
            if file_name.endswith('.csv'):
                file_data = io.StringIO(file.read().decode('utf-8'))
                reader = csv.reader(file_data)
                header = next(reader)
                data = list(reader)
            elif file_name.endswith('.xlsx'):
                wb = openpyxl.load_workbook(file)
                sheet = wb.active
                header = [cell.value for cell in list(sheet.rows)[0]]
                data = [list(row) for row in sheet.iter_rows(min_row=2, values_only=True)]
            else:
                return Response({'error': 'Unsupported file type. Please upload CSV or XLSX files.'}, status=status.HTTP_400_BAD_REQUEST)

            # Check first row to determine type
            if len(header) == 7:
                # Customer data
                customer_count = 0
                for row in data:
                    if len(row) < 7:
                        continue
                    try:
                        customer_id, first_name, last_name, age, phone_number, monthly_salary, approved_limit = row[:7]
                        Customer.objects.get_or_create(
                            customer_id=int(customer_id),
                            defaults={
                                'first_name': first_name,
                                'last_name': last_name,
                                'phone_number': phone_number,
                                'monthly_salary': float(monthly_salary),
                                'approved_limit': float(approved_limit),
                                'current_debt': 0,
                                'age': int(age),
                            }
                        )
                        customer_count += 1
                    except Exception as e:
                        pass  # Skip invalid rows
                return Response({'message': f'Customer data uploaded successfully. {customer_count} customers imported.'})
            elif len(header) == 9:
                # Loan data
                loan_count = 0
                skipped_count = 0
                for row in data:
                    if len(row) < 9:
                        continue
                    try:
                        customer_id, loan_id, loan_amount, tenure, interest_rate, monthly_repayment, emis_paid_on_time, start_date, end_date = row[:9]
                        # Handle date parsing
                        if isinstance(start_date, str):
                            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
                        elif isinstance(start_date, datetime.datetime):
                            start_date = start_date.date()
                        if isinstance(end_date, str):
                            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
                        elif isinstance(end_date, datetime.datetime):
                            end_date = end_date.date()
                        customer = Customer.objects.get(customer_id=int(customer_id))
                        Loan.objects.get_or_create(
                            loan_id=int(loan_id),
                            defaults={
                                'customer': customer,
                                'loan_amount': float(loan_amount),
                                'tenure': int(tenure),
                                'interest_rate': float(interest_rate),
                                'monthly_repayment': float(monthly_repayment),
                                'emis_paid_on_time': int(emis_paid_on_time),
                                'start_date': start_date,
                                'end_date': end_date,
                            }
                        )
                        loan_count += 1
                    except Customer.DoesNotExist:
                        skipped_count += 1
                    except Exception as e:
                        pass  # Skip invalid rows
                return Response({'message': f'Loan data uploaded successfully. {loan_count} loans imported, {skipped_count} skipped (customer not found).'})

            return Response({'message': 'Data uploaded successfully'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
