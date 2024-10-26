from django.contrib.auth.models import User
from rest_framework import serializers
from .models import TypeExpense, Expense, MonthlyInput

class TypeExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeExpense
        fields = '__all__'

class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'  # Ensure this is not a tuple
        read_only_fields = ['user']  # Only settable from the backend

class MonthlyInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyInput
        fields = '__all__'
        read_only_fields = ['user']  # Only settable from the backend

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'password']
        
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'], 
            password=validated_data['password']
        )
        return user
