from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from datetime import date
import json

class Task(models.Model):
    title = models.CharField(max_length=200)
    due_date = models.DateField()
    estimated_hours = models.FloatField(validators=[MinValueValidator(0.1)])
    importance = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    dependencies = models.JSONField(default=list, blank=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        if self.due_date < date.today():
            raise ValidationError("Due date cannot be in the past")
        if not isinstance(self.dependencies, list):
            raise ValidationError("Dependencies must be a list")
        
        for dep in self.dependencies:
            if not isinstance(dep, int):
                raise ValidationError("Dependency IDs must be integers")
    
    def __str__(self):
        return self.title

class TaskAnalysisResult(models.Model):
    tasks_data = models.JSONField()  
    analysis_results = models.JSONField()  
    strategy_used = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
