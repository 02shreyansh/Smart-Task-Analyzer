from rest_framework import serializers
from .models import Task
from datetime import date
import json

class TaskSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    title = serializers.CharField(max_length=200)
    due_date = serializers.DateField()
    estimated_hours = serializers.FloatField(min_value=0.1)
    importance = serializers.IntegerField(min_value=1, max_value=10)
    dependencies = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list
    )
    
    def validate_due_date(self, value):
        if value < date.today():
            raise serializers.ValidationError("Due date cannot be in the past")
        return value
    
    def validate_dependencies(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Dependencies must be a list")
        for dep in value:
            if not isinstance(dep, int):
                raise serializers.ValidationError("Dependency IDs must be integers")
        return value

class TaskAnalysisSerializer(serializers.Serializer):
    tasks = TaskSerializer(many=True)
    strategy = serializers.ChoiceField(
        choices=['smart_balance', 'fastest_wins', 'high_impact', 'deadline_driven'],
        default='smart_balance'
    )