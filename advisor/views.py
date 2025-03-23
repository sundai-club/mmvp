from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Destination, TravelAdvice
from .serializers import DestinationSerializer, TravelAdviceSerializer
from .services import MaestroService
import json

# Create your views here.

def home(request):
    """
    Render the home page with the travel advisor application.
    """
    return render(request, 'advisor/home.html')

class DestinationViewSet(viewsets.ModelViewSet):
    queryset = Destination.objects.all()
    serializer_class = DestinationSerializer

    @action(detail=True, methods=['post'])
    def generate_advice(self, request, pk=None):
        destination = self.get_object()
        maestro_service = MaestroService()

        try:
            # Extract optional parameters
            hobbies = None
            follow_up_question = None
            
            if request.body:
                try:
                    body_data = json.loads(request.body)
                    hobbies = body_data.get('hobbies')
                    follow_up_question = body_data.get('follow_up_question')
                except json.JSONDecodeError:
                    pass  # Body is not JSON, continue without these params
            
            # Get advice from Maestro
            maestro_response = maestro_service.get_travel_advice(
                destination.name,
                destination.country,
                hobbies=hobbies,
                follow_up_question=follow_up_question
            )

            # Parse the response into different categories
            advice_data = maestro_service.parse_advice(maestro_response)

            # Create or update advice for each category
            for category, content in advice_data.items():
                TravelAdvice.objects.update_or_create(
                    destination=destination,
                    category=category,
                    defaults={'content': content}
                )

            # Get updated destination data
            serializer = self.get_serializer(destination)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TravelAdviceViewSet(viewsets.ModelViewSet):
    queryset = TravelAdvice.objects.all()
    serializer_class = TravelAdviceSerializer
