import os
import requests
from django.conf import settings
from ai21 import AI21Client

class MaestroService:
    def __init__(self):
        self.client = AI21Client(api_key=settings.AI21_API_KEY)

    def get_travel_advice(self, destination, country, hobbies=None, follow_up_question=None):
        """
        Get travel advice for a specific destination using AI21's Maestro.
        
        Args:
            destination: The city or place name
            country: The country name
            hobbies: Optional string containing user's interests and hobbies
            follow_up_question: Optional follow-up question from the user
        """
        # Construct a more sophisticated prompt based on the parameters
        base_prompt = f"Create a detailed off-the-beaten-path travel guide for {destination}, {country}"
        
        if hobbies:
            base_prompt += f" tailored for someone interested in {hobbies}"
            
        if follow_up_question:
            base_prompt = follow_up_question
            
        # Build requirements with more specific instructions for an enhanced guide
        requirements = [
            {
                "name": "safety_section",
                "description": "Write a section titled 'SAFETY INFORMATION' with exactly 3 paragraphs about safety conditions, emergency numbers, and local precautions specific to this location. Include insights that typical tourists might not know."
            },
            {
                "name": "weather_section",
                "description": "Write a section titled 'WEATHER AND CLIMATE' with exactly 2 paragraphs about seasonal patterns, best times to visit for avoiding crowds, and local weather phenomena. Include practical clothing advice."
            },
            {
                "name": "culture_section",
                "description": "Write a section titled 'CULTURAL GUIDE' with exactly 3 paragraphs about local customs, etiquette, and traditions. Focus on lesser-known cultural aspects that create authentic experiences and respectful interaction with locals."
            },
            {
                "name": "transport_section",
                "description": "Write a section titled 'TRANSPORTATION' with exactly 2 paragraphs about getting around like a local, including hidden transportation options, shortcuts, and advice on avoiding tourist traps when traveling in the area."
            },
            {
                "name": "attractions_section",
                "description": "Write a section titled 'ATTRACTIONS AND ACTIVITIES' with exactly 3 paragraphs about unique experiences, hidden gems, and local favorites that aren't in typical guidebooks. Focus on authentic, immersive experiences instead of crowded tourist attractions."
            }
        ]
        
        # If user provided hobbies, add a specialized section for their interests
        if hobbies and not follow_up_question:
            requirements.append({
                "name": "personalized_section",
                "description": f"Write a section titled 'PERSONALIZED RECOMMENDATIONS' with exactly 2 paragraphs of recommendations specifically for travelers interested in {hobbies}. Suggest specific venues, activities, or experiences that match these interests in this location."
            })
        
        # Run the enhanced Maestro query
        run = self.client.beta.maestro.runs.create_and_poll(
            input=base_prompt,
            requirements=requirements,
            tools=[{"type": "web_search"}]
        )
        return run.result

    def parse_advice(self, maestro_response):
        """
        Parse the Maestro response into structured travel advice categories.
        """
        advice = {
            'safety': '',
            'weather': '',
            'culture': '',
            'transportation': '',
            'attractions': '',
            'personalized': ''  # New category for personalized recommendations
        }
        
        # Convert response to string if it isn't already
        response_text = str(maestro_response)
        
        # Define section markers
        section_markers = {
            'safety': 'SAFETY INFORMATION',
            'weather': 'WEATHER AND CLIMATE',
            'culture': 'CULTURAL GUIDE',
            'transportation': 'TRANSPORTATION',
            'attractions': 'ATTRACTIONS AND ACTIVITIES',
            'personalized': 'PERSONALIZED RECOMMENDATIONS'
        }
        
        # Split the text into sections
        sections = response_text.split('\n\n')
        current_section = None
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Check for section headers
            section_found = False
            for category, marker in section_markers.items():
                if marker.lower() in section.lower():
                    current_section = category
                    section_found = True
                    break
            
            # If this is a header, continue to next section
            if section_found:
                continue
                
            # Add content to current section
            if current_section and section:
                if advice[current_section]:
                    advice[current_section] += '\n\n'
                advice[current_section] += section
        
        # Clean up the sections
        for category in advice:
            if not advice[category]:
                if category == 'personalized':
                    # Skip empty personalized section
                    continue
                advice[category] = f"Information about {category} will be updated soon."
            else:
                # Remove the section header if it's at the start
                marker = section_markers.get(category, '')
                if marker and advice[category].lower().startswith(marker.lower()):
                    advice[category] = advice[category][len(marker):].strip()
        
        # Remove empty personalized section
        if not advice['personalized']:
            advice.pop('personalized', None)
            
        return advice 