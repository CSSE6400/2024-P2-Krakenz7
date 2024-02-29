from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, timedelta
 
api = Blueprint('api', __name__, url_prefix='/api/v1') 

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})


@api.route('/todos', methods=['GET'])
def get_todos():
    # Extract query parameters
    completed_query = request.args.get('completed')
    window = request.args.get('window', type=int)
    
    # Initialize the query
    query = Todo.query

    # Filter by completion status if the 'completed' parameter is provided
    if completed_query is not None:
        completed = completed_query.lower() in ['true', '1', 't']
        query = query.filter_by(completed=completed)

    # Filter by a time window if the 'window' parameter is provided
    if window is not None:
        cutoff_date = datetime.utcnow() + timedelta(days=window)
        query = query.filter(Todo.deadline_at <= cutoff_date)

    # Execute the query to get filtered todos
    todos = query.all()
    
    # Convert the todo items to dictionary format
    result = [todo.to_dict() for todo in todos]

    return jsonify(result)

@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
       return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST'])
def create_todo():
    # Define the expected fields in a todo item
    expected_fields = {'title', 'description', 'completed', 'deadline_at'}
    received_fields = set(request.json.keys())

    # Check for extra fields
    extra_fields = received_fields - expected_fields
    if extra_fields:
        return jsonify({'error': 'Extra fields provided: ' + ', '.join(extra_fields)}), 400

    # Proceed with existing validation for required fields
    if 'title' not in request.json or not request.json['title']:
        return jsonify({'error': 'Missing required field: title'}), 400

    # Create a new Todo object with validated fields
    todo = Todo(
        title=request.json['title'],
        description=request.json.get('description', ''),
        completed=request.json.get('completed', False),
    )

    if 'deadline_at' in request.json:
        todo.deadline_at = datetime.fromisoformat(request.json['deadline_at'])
    
    db.session.add(todo)
    db.session.commit()

    return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    
    # Define expected fields
    expected_fields = {'title', 'description', 'completed', 'deadline_at'}
    input_fields = set(request.json.keys())

    # Check for extra fields
    if not expected_fields.issuperset(input_fields):
        return jsonify({'error': 'Unexpected fields in request'}), 400

    # Proceed with updating the todo item as before
    todo.title = request.json.get('title', todo.title)
    todo.description = request.json.get('description', todo.description)
    todo.completed = request.json.get('completed', todo.completed)
    
    if 'deadline_at' in request.json:
        todo.deadline_at = datetime.fromisoformat(request.json['deadline_at'])
    
    db.session.commit()

    return jsonify(todo.to_dict())

@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
       return jsonify({}), 200
    
    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200
 
