from bson import ObjectId

from flask import Flask
from flask import jsonify
from flask import request
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import JWTManager
from flask_jwt_extended import jwt_required
from flask_pymongo import PyMongo
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash

from app.data_structures import UploadDocument
from app.collection_structures import Users
from app.collection_structures import Documents
from app.data_structures import Login
from app.data_structures import UploadDocument as upload_doc
from app.data_structures import Methods
from app.data_structures import ResponseMessages as mssg

app = Flask(__name__)

app.config["MONGO_URI"] = "mongodb://localhost:27017/mydb"
mongo = PyMongo(app)

app.config["JWT_SECRET_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTczMzU4ODE5OSwianRpIjoiM2U0MTBjNmEtMjhiNC00MTExLWE0NGEtNmU4NTViNzNlNDYwIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjY3NTQ3M2VmNzFhYTFlOTk3Zjc4ZjYwYiIsIm5iZiI6MTczMzU4ODE5OSwiY3NyZiI6IjdkM2MxMDQzLTAwM2QtNDE4My04MTMzLTIwMjNjYjI4NTRhMSIsImV4cCI6MTczMzU4OTA5OX0.qN3zKCaRz62YwXCwtY9HjYg2KV8iWAN541Dmm8_rWZA"
jwt = JWTManager(app)

def identify_document_type(text):
    document_types = {
        "ID Card": ["ID Number", "Date of Birth"],
        "IRS Form": ["Internal Revenue Service", "Taxpayer ID"],
        "Passport": ["Passport Number", "Nationality"],
        "Bank Statement": ["Account Number", "Transaction History"]
    }
    text = text.lower()
    for doc_type, keywords in document_types.items():
        if any(keyword.lower() in text for keyword in keywords):
            return doc_type

    return mssg.UNKNOWN

@app.route('/signup', methods=[Methods.POST])
def signup():
    data = request.get_json()
    if not data or Login.EMAIL not in data or Login.PASSWORD not in data:
        return jsonify({}), 400

    email = data[Login.EMAIL]
    password = data[Login.PASSWORD]
    if mongo.db.users.find_one({Login.EMAIL: email}):
        return jsonify({"message": mssg.USER_ALREADY_EXISTS}), 400

    hashed_password = generate_password_hash(password)
    user_id = mongo.db.users.insert_one({
        Login.EMAIL: email,
        Login.PASSWORD: hashed_password
    })
    return jsonify({"message": mssg.SIGN_UP_MESSAGE}), 201

@app.route('/login', methods=[Methods.POST])
def login():
    data = request.get_json()
    if not data or Login.EMAIL not in data or Login.PASSWORD not in data:
        return jsonify({}), 400

    email = data[Login.EMAIL]
    password = data[Login.PASSWORD]
    user = mongo.db.users.find_one({Login.EMAIL: email})
    if user and check_password_hash(user[Login.PASSWORD], password):
        access_token = create_access_token(identity=str(user[Users.ID]))
        return jsonify(access_token=access_token), 200

    return jsonify({"message": mssg.INVALID_EMAIL_OR_PASSWORD}), 401

@app.route('/upload_document', methods=[Methods.POST])
@jwt_required()
def upload_document():
    current_user = get_jwt_identity()
    data = request.get_json()
    if not data or UploadDocument.TEXT not in data or UploadDocument.PAGES not in data:
        return jsonify({"message": mssg.MISSING_REQUIRED_FIELDS}), 400

    text = data[upload_doc.TEXT]
    pages = data[upload_doc.PAGES]
    tags = data.get(upload_doc.TAGS, [])
    doc_type = identify_document_type(text)
    document = {
        Users.USER_ID: ObjectId(current_user),
        upload_doc.PAGES: pages,
        upload_doc.TEXT: text,
        upload_doc.TAGS: tags,
        Documents.DOCUMENT_TYPE: doc_type
    }
    mongo.db.documents.insert_one(document)
    return jsonify({"message": mssg.DOCUMENT_UPLOADED_SUCCESSFULLY, upload_doc.TYPE: doc_type}), 201

@app.route('/list_documents', methods=[Methods.GET])
@jwt_required()
def list_documents():
    current_user = get_jwt_identity()
    page = int(request.args.get(Documents.PAGE, 1))
    per_page = int(request.args.get(Documents.PER_PAGE, 10))
    tags_filter = request.args.get(Documents.TAGS, '').lower()
    query = {Documents.USER_ID: ObjectId(current_user)}
    if tags_filter:
        query[Documents.TAGS] = {"$regex": tags_filter, "$options": "i"}
    documents = mongo.db.documents.find(query).skip((page - 1) * per_page).limit(per_page)
    doc_list = []
    for doc in documents:
        doc[Documents.ID] = str(doc[Documents.ID])
        doc[Documents.USER_ID] = str(doc[Documents.USER_ID])
        doc_list.append(doc)
    return jsonify(doc_list), 200

@app.route('/update_document/<doc_id>', methods=[Methods.PUT])
@jwt_required()
def update_document(doc_id: str) -> tuple:
    current_user = get_jwt_identity()
    document = mongo.db.documents.find_one({Documents.ID: ObjectId(doc_id), Documents.USER_ID: ObjectId(current_user)})
    if not document:
        return jsonify({"message": mssg.DOCUMENT_NOT_FOUND}), 404

    data = request.get_json()
    tags = data.get(Documents.TAGS)
    mongo.db.documents.update_one(
        {Documents.ID: ObjectId(doc_id)},
        {"$set": {Documents.TAGS: tags}})

    return jsonify({"message": mssg.DOCUMENT_UPDATED_SUCCESSFULLY}), 200

@app.route('/delete_document/<doc_id>', methods=[Methods.DELETE])
@jwt_required()
def delete_document(doc_id):
    current_user = get_jwt_identity()
    document = mongo.db.documents.find_one({
        Documents.ID: ObjectId(doc_id),
        Users.USER_ID: ObjectId(current_user)
    })
    if not document:
        return jsonify({"message": mssg.DOCUMENT_NOT_FOUND }), 404

    mongo.db.documents.delete_one({Documents.ID: ObjectId(doc_id)})
    return jsonify({"message": mssg.DOCUMENT_DELETED_SUCCESSFULLY}), 200

if __name__ == '__main__':
    app.run(debug=True)
