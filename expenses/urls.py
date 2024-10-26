from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterUserView, TypeExpenseViewSet, data_per_graph, MonthlyInputViewSet, get_total_expense_per_month, ExpenseViewSet, get_non_necessary_expense, test_view
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'type-expenses', TypeExpenseViewSet)
router.register(r'expenses', ExpenseViewSet)
router.register(r'monthly-inputs', MonthlyInputViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('no-necessary/', get_non_necessary_expense),
    path('totalExpense/', get_total_expense_per_month),
    
    path('data_per_graph/', data_per_graph),
    path('register/', RegisterUserView.as_view(), name='register'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
