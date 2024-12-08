import pytest
from app.main import app, mongo, Documents, Login, mssg


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['MONGO_URI'] = 'mongodb://localhost:27017/mydb'
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers(client):
    # Register a test user
    email = "arshtest1@gmail.com"
    password = "password123"
    client.post('/signup', json={Login.EMAIL: email, Login.PASSWORD: password})

    # Login to get a JWT token
    response = client.post('/login', json={Login.EMAIL: email, Login.PASSWORD: password})
    access_token = response.json['access_token']
    return {'Authorization': f'Bearer {access_token}'}


def test_signup(client):
    # Test valid signup
    response = client.post('/signup', json={
        'email': 'arshtest1@gmail.com',
        'password': 'password123'
    })
    assert response.status_code == 201
    assert response.json['message'] == mssg.SIGN_UP_MESSAGE

    # Test signup with missing fields
    response = client.post('/signup', json={Login.EMAIL: "arshtest@gmail.com"})
    assert response.status_code == 400

    # Test signup with existing email
    client.post('/signup', json={Login.EMAIL: "arshtest@example.com", Login.PASSWORD: "password123"})
    response = client.post('/signup', json={Login.EMAIL: "existinguser@example.com", Login.PASSWORD: "password123"})
    assert response.status_code == 400
    assert response.json['message'] == mssg.USER_ALREADY_EXISTS


def test_login(client):
    # Test valid login
    response = client.post('/login', json={Login.EMAIL: "testuser@example.com", Login.PASSWORD: "password123"})
    assert response.status_code == 200
    assert 'access_token' in response.json

    # Test login with invalid credentials
    response = client.post('/login', json={Login.EMAIL: "testuser@example.com", Login.PASSWORD: "wrongpassword"})
    assert response.status_code == 401
    assert response.json['message'] == mssg.INVALID_EMAIL_OR_PASSWORD

    # Test login with missing fields
    response = client.post('/login', json={Login.EMAIL: "testuser@example.com"})
    assert response.status_code == 400


def test_upload_document(client, auth_headers):
    # Test document upload with valid data
    document_data = {
        'text': 'My name is John Doe and my ID number is 123456789.',
        'pages': 2,
        'tags': ['identity', 'id card']
    }
    response = client.post('/upload_document', json=document_data, headers=auth_headers)
    assert response.status_code == 201
    assert response.json['message'] == mssg.DOCUMENT_UPLOADED_SUCCESSFULLY

    # Test document upload with missing required fields
    response = client.post('/upload_document', json={'text': 'Transaction History'}, headers=auth_headers)
    assert response.status_code == 400
    assert 'message' in response.json

    # Test document upload without JWT token
    response = client.post('/upload_document', json=document_data)
    assert response.status_code == 401


def test_list_documents(client, auth_headers):
    # Test document listing
    response = client.get('/list_documents', headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json, list)

    # Test document listing with tag filter
    response = client.get('/list_documents?tags=id%20card', headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_update_document(client, auth_headers):
    # Insert a document for testing
    document_data = {
        'text': 'My name is John Doe and my ID number is 123456789.',
        'pages': 2,
        'tags': ['identity', 'id card']
    }
    client.post('/upload_document', json=document_data, headers=auth_headers)
    document = mongo.db.documents.find_one({'text': document_data['text']})

    # Test valid document update
    update_data = {'tags': ['updated tag']}
    response = client.put(f'/update_document/{str(document[Documents.ID])}', json=update_data, headers=auth_headers)
    assert response.status_code == 200
    assert response.json['message'] == mssg.DOCUMENT_UPDATED_SUCCESSFULLY

    # Test document not found
    response = client.put('/update_document/nonexistent_id', json=update_data, headers=auth_headers)
    assert response.status_code == 404
    assert response.json['message'] == mssg.DOCUMENT_NOT_FOUND


def test_delete_document(client, auth_headers):
    # Insert a document for testing
    document_data = {
        'text': 'My name is John Doe and my ID number is 123456789.',
        'pages': 2,
        'tags': ['identity', 'id card']
    }
    client.post('/upload_document', json=document_data, headers=auth_headers)
    document = mongo.db.documents.find_one({'text': document_data['text']})

    # Test document deletion
    response = client.delete(f'/delete_document/{document[Documents.ID]}', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['message'] == mssg.DOCUMENT_DELETED_SUCCESSFULLY

    # Test document not found
    response = client.delete('/delete_document/nonexistent_id', headers=auth_headers)
    assert response.status_code == 404
    assert response.json['message'] == mssg.DOCUMENT_NOT_FOUND
