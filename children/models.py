# children/models.py
from django.db import models

class Child(models.Model):
    family = models.ForeignKey(
        "families.Family",
        on_delete=models.CASCADE,
        related_name="children",
    )
    name = models.CharField(max_length=30)
    image = models.ImageField(upload_to="children/")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name