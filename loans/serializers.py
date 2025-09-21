from rest_framework import serializers
from .models import Customer, Loan


class CustomerSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    monthly_income = serializers.IntegerField(source='monthly_salary', read_only=True)

    class Meta:
        model = Customer
        fields = ['customer_id', 'name', 'age', 'monthly_income', 'approved_limit', 'phone_number']

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class LoanSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()
    monthly_installment = serializers.DecimalField(source='monthly_repayment', read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = Loan
        fields = ['loan_id', 'customer', 'loan_amount', 'interest_rate', 'monthly_installment', 'tenure']


class LoanListSerializer(serializers.ModelSerializer):
    monthly_installment = serializers.DecimalField(source='monthly_repayment', read_only=True, max_digits=10, decimal_places=2)
    repayments_left = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = ['loan_id', 'loan_amount', 'interest_rate', 'monthly_installment', 'repayments_left']

    def get_repayments_left(self, obj):
        # Assuming tenure is total months, emis_paid_on_time is paid
        return obj.tenure - obj.emis_paid_on_time