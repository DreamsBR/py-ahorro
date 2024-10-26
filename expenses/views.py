from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from .models import Expense, TypeExpense, MonthlyInput
from .serializers import RegisterSerializer, ExpenseSerializer, TypeExpenseSerializer, MonthlyInputSerializer
from rest_framework.response import Response
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated


class TypeExpenseViewSet(viewsets.ModelViewSet):
    queryset = TypeExpense.objects.all()
    serializer_class = TypeExpenseSerializer


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()  # Add this line
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]  # Require authentication

    def get_queryset(self):
        # Filter expenses by the authenticated user
        return Expense.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Assign the authenticated user to the created expense
        serializer.save(user=self.request.user)



class MonthlyInputViewSet(viewsets.ModelViewSet):
    queryset = MonthlyInput.objects.all()
    serializer_class = MonthlyInputSerializer

@api_view(['GET'])
def get_non_necessary_expense(request):
    # Filtrar gastos no necesarios por el usuario autenticado
    non_necessary_expenses = Expense.objects.filter(necessary=False, user=request.user)
    serializer = ExpenseSerializer(non_necessary_expenses, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def test_view(request):
    return Response({"message": "API is working!"})


from django.db.models import DateField
from django.db.models.functions import TruncMonth

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_total_expense_per_month(request):
    total_expenses = (
        Expense.objects.filter(user=request.user)
        .annotate(month=TruncMonth('created_at'))  # Assuming you have a created_at field
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    return Response(total_expenses)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def data_per_graph(request):
    # Filtrar gastos por el usuario autenticado y agrupar por tipo
    expenses_by_type = Expense.objects.filter(user=request.user).values('type_expense__name').annotate(total_amount=Sum('amount'))
    data = [{'value': expense['total_amount'], 'name': expense['type_expense__name']} for expense in expenses_by_type]
    return Response(data)


class RegisterUserView(APIView):
    permission_classes = [AllowAny]  # Permitir acceso sin autenticación

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Usuario registrado con éxito"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
