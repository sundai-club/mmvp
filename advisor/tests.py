from django.test import TestCase, Client
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Destination, TravelAdvice
from unittest.mock import patch
from django.urls import reverse
from .services import MaestroService

# Create your tests here.

class DestinationTests(APITestCase):
    def setUp(self):
        self.destination = Destination.objects.create(
            name='Paris',
            country='France',
            description='The City of Light'
        )

    def test_create_destination(self):
        """
        Ensure we can create a new destination object.
        """
        url = '/api/destinations/'
        data = {
            'name': 'London',
            'country': 'United Kingdom',
            'description': 'The Big Smoke'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Destination.objects.count(), 2)
        self.assertEqual(Destination.objects.get(name='London').country, 'United Kingdom')

    @patch('advisor.services.MaestroService.get_travel_advice')
    @patch('advisor.services.MaestroService.parse_advice')
    def test_generate_advice(self, mock_parse_advice, mock_get_travel_advice):
        """
        Ensure we can generate travel advice for a destination.
        """
        # Mock the Maestro service responses
        mock_get_travel_advice.return_value = {'some': 'response'}
        mock_parse_advice.return_value = {
            'safety': 'Very safe city',
            'weather': 'Best visited in spring',
            'culture': 'Rich in art and history',
            'transportation': 'Excellent metro system',
            'attractions': 'Eiffel Tower, Louvre'
        }

        url = f'/api/destinations/{self.destination.id}/generate_advice/'
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(TravelAdvice.objects.count(), 5)  # One for each category
        
        # Verify that the advice was created correctly
        safety_advice = TravelAdvice.objects.get(
            destination=self.destination,
            category='safety'
        )
        self.assertEqual(safety_advice.content, 'Very safe city')

class HomeViewTest(TestCase):
    """
    Tests for the home view.
    """
    def setUp(self):
        self.client = Client()
        
    def test_home_view(self):
        """
        Test that the home view returns a 200 status code.
        """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'advisor/home.html')
