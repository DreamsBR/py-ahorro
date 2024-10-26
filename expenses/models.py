from django.db import models
from django.contrib.auth.models import User

class TypeExpense(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class Expense(models.Model):
    necessary = models.BooleanField()
    amount = models.FloatField()
    date = models.DateField(auto_now_add=True)
    type_expense = models.ForeignKey(TypeExpense, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f"Expense of {self.amount} ({'Necessary' if self.necessary else 'Unnecessary'})"

class MonthlyInput(models.Model):
    amountInput = models.FloatField()
    description = models.TextField()
    date = models.DateField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.description  # Corrige el retorno para un nombre legible
