import re
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from .models import Expense, TypeExpense, MonthlyInput
from .serializers import RegisterSerializer, ExpenseSerializer, TypeExpenseSerializer, MonthlyInputSerializer
from rest_framework.response import Response
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
# expenses/views.py (añadir al inicio del archivo)
# Backend (Django) - improved interpreter
import spacy
from typing import Dict, Optional, Any

class VoiceCommandInterpreter:
    def __init__(self):
        self.nlp = spacy.load("es_core_news_md")
        # Common category mappings
        self.category_mapping = {
            'comida': ['comida', 'alimentacion', 'alimentos', 'restaurant', 'restaurante', 'almuerzo', 'cena', 'desayuno'],
            'transporte': ['transporte', 'movilidad', 'taxi', 'bus', 'pasaje', 'gasolina', 'combustible'],
            'servicios': ['servicios', 'luz', 'agua', 'gas', 'internet', 'telefono', 'celular'],
            'entretenimiento': ['entretenimiento', 'cine', 'peliculas', 'juegos', 'netflix', 'spotify'],
            'salud': ['salud', 'medicina', 'doctor', 'medico', 'farmacia', 'hospital'],
            # Add more mappings as needed
        }

    def _extract_amount(self, text: str) -> Optional[float]:
        """Extract amount from text with improved pattern matching."""
        # Match different money formats
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:soles?|s\/\.?|pen)",  # 100 soles, 100 s/, 100 s.
            r"s\/\.?\s*(\d+(?:\.\d+)?)",  # s/100, s./ 100
            r"(\d+(?:\.\d+)?)\s*(?:nuevo?s?\s*soles?)",  # 100 nuevos soles
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1))
        return None

    def _determine_necessity(self, text: str) -> bool:
        """Determine if expense is necessary with improved detection."""
        unnecessary_indicators = [
            'innecesario', 'no necesario', 'prescindible', 
            'opcional', 'lujo', 'capricho', 'gusto'
        ]
        return not any(indicator in text.lower() for indicator in unnecessary_indicators)

    def _find_category(self, text: str, valid_categories: list) -> Optional[str]:
        """Find category with improved matching and validation."""
        doc = self.nlp(text.lower())
        normalized_text = text.lower()
        
        # 1. Direct match with valid categories
        for category in valid_categories:
            if category.lower() in normalized_text:
                return category

        # 2. Check category mappings
        for category, keywords in self.category_mapping.items():
            if any(keyword in normalized_text for keyword in keywords):
                matching_category = next(
                    (c for c in valid_categories if c.lower() == category),
                    None
                )
                if matching_category:
                    return matching_category

        # 3. NER-based detection
        for ent in doc.ents:
            if ent.label_ in ["MISC", "ORG"]:
                # Validate against valid categories
                closest_match = self._find_closest_match(ent.text, valid_categories)
                if closest_match:
                    return closest_match

        return None

    def _find_closest_match(self, text: str, valid_categories: list) -> Optional[str]:
        """Find the closest matching category using spaCy similarity."""
        text_doc = self.nlp(text.lower())
        max_similarity = 0
        best_match = None

        for category in valid_categories:
            category_doc = self.nlp(category.lower())
            similarity = text_doc.similarity(category_doc)
            
            if similarity > max_similarity and similarity > 0.6:  # Threshold for minimum similarity
                max_similarity = similarity
                best_match = category

        return best_match

    def interpret_command(self, text: str, valid_categories: list) -> Dict[str, Any]:
        """Main method to interpret voice commands."""
        if not text:
            return {
                "necesario": True,
                "monto": None,
                "categoria": None,
                "error": "No se recibió ningún texto para procesar."
            }

        # Extract amount
        monto = self._extract_amount(text)
        if not monto:
            return {
                "necesario": True,
                "monto": None,
                "categoria": None,
                "error": "No se pudo identificar el monto en el comando."
            }

        # Determine if necessary
        necesario = self._determine_necessity(text)

        # Find category
        categoria = self._find_category(text, valid_categories)
        
        if not categoria:
            return {
                "necesario": necesario,
                "monto": monto,
                "categoria": None,
                "error": "No se pudo identificar una categoría válida en el comando."
            }

        return {
            "necesario": necesario,
            "monto": monto,
            "categoria": categoria,
            "error": None
        }

# Usage in views.py
class ProcessVoiceCommand(APIView):
    def post(self, request):
        texto = request.data.get("texto")
        if not texto:
            return Response(
                {"error": "No se recibió ningún texto."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener categorías válidas de la base de datos
        valid_categories = list(TypeExpense.objects.values_list('name', flat=True))
        
        # Crear una instancia del intérprete y procesar el comando
        interpreter = VoiceCommandInterpreter()
        resultado = interpreter.interpret_command(texto, valid_categories)

        # Verificar si se identificó correctamente el monto y la categoría
        if resultado["error"]:
            return Response(resultado, status=status.HTTP_400_BAD_REQUEST)

        # Si el resultado es válido, guardar el gasto en la base de datos
        try:
            Expense.objects.create(
                amount=resultado["monto"],
                necessary=resultado["necesario"],
                type_expense=TypeExpense.objects.get(name=resultado["categoria"]),  # Asegúrate de que esta categoría existe
                user=request.user  # Asigna el usuario autenticado
            )
            return Response({"message": "Gasto guardado con éxito."}, status=status.HTTP_201_CREATED)
        except TypeExpense.DoesNotExist:
            return Response({"error": "Categoría no válida."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
