from rest_framework.test import APITestCase
from django.urls import reverse
from .models import Customer, Loan


class LoanAPITestCase(APITestCase):
    def test_register_customer(self):
        url = reverse('register')
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'age': 30,
            'monthly_income': 50000,
            'phone_number': '1234567890'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('customer_id', response.data)
        self.assertEqual(response.data['approved_limit'], '1800000.00')

    def test_check_eligibility(self):
        # Create customer first
        customer = Customer.objects.create(
            customer_id=1,
            first_name='Jane',
            last_name='Doe',
            age=25,
            monthly_salary=40000,
            approved_limit=1440000,
            phone_number='0987654321'
        )
        url = reverse('check-eligibility')
        data = {
            'customer_id': 1,
            'loan_amount': 100000,
            'interest_rate': 10,
            'tenure': 12
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('approval', response.data)
