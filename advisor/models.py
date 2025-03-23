from django.db import models

# Create your models here.

class Destination(models.Model):
    name = models.CharField(max_length=200)
    country = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}, {self.country}"

class TravelAdvice(models.Model):
    destination = models.ForeignKey(Destination, on_delete=models.CASCADE, related_name='advice')
    category = models.CharField(max_length=100)  # e.g., 'safety', 'weather', 'culture', 'transportation'
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category} advice for {self.destination.name}"
