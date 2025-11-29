from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from datetime import datetime, date
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .serializers import TaskSerializer, TaskAnalysisSerializer
from .algorithms import StrategyFactory
from .models import TaskAnalysisResult
import json

@api_view(['POST'])
@csrf_exempt
def analyze_tasks(request):
    try:
        if isinstance(request.data, str):
            data = json.loads(request.data)
        else:
            data = request.data
        
        print("Parsed data:", data) 
        
        tasks_data = data.get('tasks', [])
        strategy = data.get('strategy', 'smart_balance')
        
        if not tasks_data:
            return Response(
                {'error': 'No tasks provided', 'details': 'Tasks array is empty'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for i, task in enumerate(tasks_data):
            if not all(key in task for key in ['title', 'due_date', 'estimated_hours', 'importance']):
                return Response(
                    {'error': f'Task {i} missing required fields', 
                     'required_fields': ['title', 'due_date', 'estimated_hours', 'importance']},
                    status=status.HTTP_400_BAD_REQUEST
                )

        algorithm = StrategyFactory.get_algorithm(strategy)
        circular_deps = algorithm.detect_circular_dependencies(tasks_data)
        if circular_deps:
            return Response({
                'error': 'Circular dependencies detected',
                'circular_dependencies': circular_deps
            }, status=status.HTTP_400_BAD_REQUEST)

        analyzed_tasks = []
        for task in tasks_data:
            analysis_result = algorithm.calculate_priority_score(task, tasks_data)
            
            analyzed_task = {
                **task,
                'priority_score': analysis_result['total_score'],
                'component_scores': analysis_result['component_scores'],
                'explanation': analysis_result['explanation']
            }
            analyzed_tasks.append(analyzed_task)
        analyzed_tasks.sort(key=lambda x: x['priority_score'], reverse=True)
        for task in analyzed_tasks:
            if 'due_date' in task and isinstance(task['due_date'], date):
                task['due_date'] = task['due_date'].isoformat()
        
        response_data = {
            'strategy_used': strategy,
            'tasks': analyzed_tasks,
            'total_tasks': len(analyzed_tasks),
            'analysis_date': datetime.now().isoformat()  
        }
        return Response(response_data)
        
    except json.JSONDecodeError as e:
        return Response(
            {'error': 'Invalid JSON format', 'details': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': f'Analysis failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def suggest_tasks(request):
    try:
        return Response({
            'message': 'Use the POST /api/tasks/analyze/ endpoint with your tasks data, then select top 3 from results',
            'example_usage': {
                'method': 'POST /api/tasks/analyze/',
                'payload': {
                    'tasks': [
                        {
                            'title': 'Task name',
                            'due_date': '2024-12-31',
                            'estimated_hours': 2,
                            'importance': 8,
                            'dependencies': []
                        }
                    ],
                    'strategy': 'smart_balance'
                }
            }
        })
        
    except Exception as e:
        return Response(
            {'error': f'Suggestion failed: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
def validate_tasks(request):
    serializer = TaskSerializer(data=request.data, many=True)
    
    if serializer.is_valid():
        return Response({
            'valid': True,
            'message': 'All tasks are valid',
            'task_count': len(serializer.validated_data)
        })
    else:
        return Response({
            'valid': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
