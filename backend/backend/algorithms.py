from datetime import date, datetime
from typing import List, Dict, Any
import math

class TaskPriorityAlgorithm:
    def __init__(self, weights=None):
        self.weights = weights or {
            'urgency': 0.35,
            'importance': 0.30,
            'effort': 0.20,
            'dependencies': 0.15
        }
    
    def calculate_urgency_score(self, due_date: str, today: date = None) -> float:
        if today is None:
            today = date.today()
        if isinstance(due_date, str):
            due_date_obj = date.fromisoformat(due_date)
        elif isinstance(due_date, date):
            due_date_obj = due_date
        else:
            due_date_obj = date.fromisoformat(str(due_date))
        
        days_until_due = (due_date_obj - today).days
        if days_until_due < 0:
            return 1.0 
        elif days_until_due == 0:
            return 0.9
        elif days_until_due <= 1:
            return 0.8
        elif days_until_due <= 3:
            return 0.6
        elif days_until_due <= 7:
            return 0.4
        else:
            return max(0.1, 1.0 / (1.0 + math.log(days_until_due - 6)))
    
    def calculate_effort_score(self, estimated_hours: float) -> float:
        if estimated_hours <= 1:
            return 1.0
        elif estimated_hours <= 4:
            return 0.8
        elif estimated_hours <= 8:
            return 0.6
        elif estimated_hours <= 16:
            return 0.4
        else:
            return 0.2
    
    def calculate_dependency_score(self, dependencies: List[int], all_tasks: List[Dict]) -> float:
        if not dependencies:
            return 0.3 
        blocking_count = 0
        current_task_ids = [task.get('id') for task in all_tasks if task.get('id')]
        
        for task in all_tasks:
            task_deps = task.get('dependencies', [])
            for dep_id in task_deps:
                if dep_id in current_task_ids:
                    blocking_count += 1
        
        if blocking_count > 0:
            return min(1.0, 0.5 + (blocking_count * 0.1))
        else:
            return 0.3
    
    def detect_circular_dependencies(self, tasks: List[Dict]) -> List[List[int]]:
        graph = {}
        task_ids = [task.get('id', i) for i, task in enumerate(tasks)]
        for i, task in enumerate(tasks):
            task_id = task.get('id', i)
            graph[task_id] = task.get('dependencies', [])
        
        def dfs(node, visited, stack, path):
            visited[node] = True
            stack[node] = True
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, visited, stack, path.copy()):
                        return True
                elif stack[neighbor]:
                    circular_path = path[path.index(neighbor):]
                    circular_path.append(neighbor)
                    circular_dependencies.append(circular_path)
                    return True
            
            stack[node] = False
            return False
        
        visited = {node: False for node in graph}
        stack = {node: False for node in graph}
        circular_dependencies = []
        
        for node in graph:
            if not visited[node]:
                dfs(node, visited, stack, [])
        
        return circular_dependencies
    
    def calculate_priority_score(self, task: Dict, all_tasks: List[Dict]) -> Dict:
        try:
            due_date = task['due_date']
            urgency_score = self.calculate_urgency_score(due_date)
            importance_score = task['importance'] / 10.0  
            effort_score = self.calculate_effort_score(task['estimated_hours'])
            dependency_score = self.calculate_dependency_score(
                task.get('dependencies', []), all_tasks
            )
            total_score = (
                urgency_score * self.weights['urgency'] +
                importance_score * self.weights['importance'] +
                effort_score * self.weights['effort'] +
                dependency_score * self.weights['dependencies']
            )
            
            return {
                'total_score': round(total_score, 3),
                'component_scores': {
                    'urgency': round(urgency_score, 3),
                    'importance': round(importance_score, 3),
                    'effort': round(effort_score, 3),
                    'dependencies': round(dependency_score, 3)
                },
                'explanation': self.generate_explanation(
                    urgency_score, importance_score, effort_score, dependency_score
                )
            }
        except Exception as e:
            return {
                'total_score': 0,
                'component_scores': {'urgency': 0, 'importance': 0, 'effort': 0, 'dependencies': 0},
                'explanation': f'Error calculating score: {str(e)}'
            }
    
    def generate_explanation(self, urgency: float, importance: float, 
                           effort: float, dependencies: float) -> str:
        explanations = []
        
        if urgency > 0.8:
            explanations.append("very urgent deadline")
        elif urgency > 0.6:
            explanations.append("approaching deadline")
        
        if importance > 0.8:
            explanations.append("high importance")
        elif importance > 0.6:
            explanations.append("moderate importance")
        
        if effort > 0.8:
            explanations.append("quick win (low effort)")
        elif effort > 0.6:
            explanations.append("moderate effort")
        
        if dependencies > 0.6:
            explanations.append("blocks other tasks")
        elif dependencies > 0.4:
            explanations.append("has dependencies")
        
        if not explanations:
            return "Moderate priority across all factors"
        
        return "High priority due to " + ", ".join(explanations)

class StrategyFactory:
    @staticmethod
    def get_algorithm(strategy: str) -> TaskPriorityAlgorithm:
        strategies = {
            'smart_balance': TaskPriorityAlgorithm({
                'urgency': 0.35, 'importance': 0.30, 'effort': 0.20, 'dependencies': 0.15
            }),
            'fastest_wins': TaskPriorityAlgorithm({
                'urgency': 0.20, 'importance': 0.25, 'effort': 0.45, 'dependencies': 0.10
            }),
            'high_impact': TaskPriorityAlgorithm({
                'urgency': 0.25, 'importance': 0.50, 'effort': 0.15, 'dependencies': 0.10
            }),
            'deadline_driven': TaskPriorityAlgorithm({
                'urgency': 0.60, 'importance': 0.20, 'effort': 0.10, 'dependencies': 0.10
            })
        }
        return strategies.get(strategy, strategies['smart_balance'])