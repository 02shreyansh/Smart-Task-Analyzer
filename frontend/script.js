class TaskManager {
    constructor() {
        this.tasks = [];
        this.apiBaseUrl = 'http://localhost:8000/api/tasks';
        this.init();
    }

    init() {
        this.loadTasksFromStorage();
        this.renderTasks();
        this.setMinDate();
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('taskForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addTaskFromForm();
        });
    }

    setMinDate() {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('dueDate').min = today;
    }

    addTaskFromForm() {
        const formData = new FormData(document.getElementById('taskForm'));
        
        const dependenciesInput = document.getElementById('dependencies').value;
        const dependencies = dependenciesInput 
            ? dependenciesInput.split(',').map(id => parseInt(id.trim())).filter(id => !isNaN(id))
            : [];

        const task = {
            title: document.getElementById('title').value,
            due_date: document.getElementById('dueDate').value,
            estimated_hours: parseFloat(document.getElementById('estimatedHours').value),
            importance: parseInt(document.getElementById('importance').value),
            dependencies: dependencies
        };

        if (this.validateTask(task)) {
            task.id = this.tasks.length > 0 ? Math.max(...this.tasks.map(t => t.id)) + 1 : 1;
            this.tasks.push(task);
            this.saveTasksToStorage();
            this.renderTasks();
            document.getElementById('taskForm').reset();
            this.setMinDate();
        }
    }

    validateTask(task) {
        if (!task.title.trim()) {
            this.showMessage('Task title is required', 'error');
            return false;
        }

        if (!task.due_date) {
            this.showMessage('Due date is required', 'error');
            return false;
        }

        if (task.estimated_hours <= 0) {
            this.showMessage('Estimated hours must be greater than 0', 'error');
            return false;
        }

        if (task.importance < 1 || task.importance > 10) {
            this.showMessage('Importance must be between 1 and 10', 'error');
            return false;
        }

        return true;
    }

    loadBulkTasks() {
        const bulkInput = document.getElementById('bulkInput').value;
        
        if (!bulkInput.trim()) {
            this.showMessage('Please enter JSON data', 'error');
            return;
        }

        try {
            const tasks = JSON.parse(bulkInput);
            
            if (!Array.isArray(tasks)) {
                throw new Error('Input must be an array of tasks');
            }

            let validTasks = [];
            let errors = [];

            tasks.forEach((task, index) => {
                if (!task.id) {
                    task.id = this.tasks.length + index + 1;
                }

                if (this.validateTask(task)) {
                    validTasks.push(task);
                } else {
                    errors.push(`Task ${index + 1}: Invalid data`);
                }
            });

            if (validTasks.length > 0) {
                this.tasks.push(...validTasks);
                this.saveTasksToStorage();
                this.renderTasks();
                this.showMessage(`Loaded ${validTasks.length} tasks successfully${errors.length > 0 ? ` (${errors.length} errors)` : ''}`, 'success');
            } else {
                this.showMessage('No valid tasks found in input', 'error');
            }

        } catch (error) {
            this.showMessage('Invalid JSON format: ' + error.message, 'error');
        }
    }

    async analyzeTasks() {
        if (this.tasks.length === 0) {
            this.showMessage('No tasks to analyze', 'error');
            return;
        }

        const strategy = document.getElementById('strategySelect').value;
        const analyzeBtn = document.getElementById('analyzeBtn');
        const loading = document.getElementById('loading');

        analyzeBtn.disabled = true;
        loading.classList.remove('hidden');

        try {
            const response = await fetch(`${this.apiBaseUrl}/analyze/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    tasks: this.tasks,
                    strategy: strategy
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Analysis failed');
            }

            this.displayResults(data);

        } catch (error) {
            this.showMessage('Analysis failed: ' + error.message, 'error');
        } finally {
            analyzeBtn.disabled = false;
            loading.classList.add('hidden');
        }
    }

    displayResults(data) {
        const resultsContainer = document.getElementById('results');
        
        if (!data.tasks || data.tasks.length === 0) {
            resultsContainer.innerHTML = '<div class="error-message">No results to display</div>';
            return;
        }

        let html = `
            <div class="results-header">
                <h3>Analysis Results (${data.strategy_used.replace('_', ' ')})</h3>
                <p>Analyzed ${data.total_tasks} tasks on ${new Date(data.analysis_date).toLocaleString()}</p>
            </div>
        `;

        data.tasks.forEach((task, index) => {
            const priorityClass = this.getPriorityClass(task.priority_score);
            const priorityLabel = this.getPriorityLabel(task.priority_score);
            
            html += `
                <div class="result-item ${priorityClass}">
                    <div class="result-header">
                        <div class="result-title">${index + 1}. ${task.title}</div>
                        <div class="priority-info">
                            <span class="priority-badge badge-${priorityLabel.toLowerCase()}">${priorityLabel}</span>
                            <span class="score-display">${task.priority_score}</span>
                        </div>
                    </div>
                    
                    <div class="result-details">
                        <div class="detail-item">
                            <div class="detail-label">Due Date</div>
                            <div class="detail-value">${new Date(task.due_date).toLocaleDateString()}</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Effort</div>
                            <div class="detail-value">${task.estimated_hours}h</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Importance</div>
                            <div class="detail-value">${task.importance}/10</div>
                        </div>
                        <div class="detail-item">
                            <div class="detail-label">Dependencies</div>
                            <div class="detail-value">${task.dependencies.length}</div>
                        </div>
                    </div>

                    <div class="component-scores">
                        <div class="component-score">
                            <div>Urgency</div>
                            <strong>${task.component_scores.urgency}</strong>
                        </div>
                        <div class="component-score">
                            <div>Importance</div>
                            <strong>${task.component_scores.importance}</strong>
                        </div>
                        <div class="component-score">
                            <div>Effort</div>
                            <strong>${task.component_scores.effort}</strong>
                        </div>
                        <div class="component-score">
                            <div>Dependencies</div>
                            <strong>${task.component_scores.dependencies}</strong>
                        </div>
                    </div>

                    <div class="explanation">
                        <strong>Why:</strong> ${task.explanation}
                    </div>
                </div>
            `;
        });

        resultsContainer.innerHTML = html;
    }

    getPriorityClass(score) {
        if (score >= 0.7) return 'priority-high';
        if (score >= 0.4) return 'priority-medium';
        return 'priority-low';
    }

    getPriorityLabel(score) {
        if (score >= 0.7) return 'High';
        if (score >= 0.4) return 'Medium';
        return 'Low';
    }

    renderTasks() {
        const tasksList = document.getElementById('tasksList');
        const taskCount = document.getElementById('taskCount');

        if (this.tasks.length === 0) {
            tasksList.innerHTML = '<div class="placeholder">No tasks added yet</div>';
            taskCount.textContent = '0 tasks';
            return;
        }

        taskCount.textContent = `${this.tasks.length} task${this.tasks.length !== 1 ? 's' : ''}`;

        tasksList.innerHTML = this.tasks.map(task => `
            <div class="task-item">
                <div class="task-info">
                    <div class="task-title">${task.title}</div>
                    <div class="task-details">
                        Due: ${new Date(task.due_date).toLocaleDateString()} | 
                        Effort: ${task.estimated_hours}h | 
                        Importance: ${task.importance}/10 |
                        Dependencies: ${task.dependencies.length}
                    </div>
                </div>
                <button onclick="taskManager.removeTask(${task.id})" class="remove-btn">Remove</button>
            </div>
        `).join('');
    }

    removeTask(taskId) {
        this.tasks = this.tasks.filter(task => task.id !== taskId);
        this.saveTasksToStorage();
        this.renderTasks();
    }

    clearAllTasks() {
        if (this.tasks.length === 0) return;
        
        if (confirm('Are you sure you want to clear all tasks?')) {
            this.tasks = [];
            this.saveTasksToStorage();
            this.renderTasks();
            this.showMessage('All tasks cleared', 'success');
        }
    }

    showMessage(message, type = 'info') {
        const existingMessages = document.querySelectorAll('.message');
        existingMessages.forEach(msg => msg.remove());

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        messageDiv.textContent = message;

        document.querySelector('.app-container').insertBefore(messageDiv, document.querySelector('.analysis-controls'));
        setTimeout(() => {
            messageDiv.remove();
        }, 5000);
    }

    saveTasksToStorage() {
        localStorage.setItem('smartTasks', JSON.stringify(this.tasks));
    }

    loadTasksFromStorage() {
        const saved = localStorage.getItem('smartTasks');
        if (saved) {
            try {
                this.tasks = JSON.parse(saved);
            } catch (e) {
                console.error('Error loading tasks from storage:', e);
                this.tasks = [];
            }
        }
    }
}
function loadBulkTasks() {
    taskManager.loadBulkTasks();
}

function analyzeTasks() {
    taskManager.analyzeTasks();
}

function clearAllTasks() {
    taskManager.clearAllTasks();
}

const taskManager = new TaskManager();