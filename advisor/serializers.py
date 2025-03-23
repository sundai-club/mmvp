from rest_framework import serializers
from .models import Destination, TravelAdvice

class TravelAdviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TravelAdvice
        fields = ['id', 'category', 'content', 'created_at', 'updated_at']

class DestinationSerializer(serializers.ModelSerializer):
    advice = TravelAdviceSerializer(many=True, read_only=True)

    class Meta:
        model = Destination
        fields = ['id', 'name', 'country', 'description', 'advice', 'created_at', 'updated_at'] 