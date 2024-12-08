class Login:
    EMAIL = "email"
    PASSWORD = "password"

class UploadDocument:
    TEXT = "text"
    PAGES = "pages"
    TAGS = "tags"
    TYPE = "type"

class Methods:
    POST = "POST"
    GET = "GET"
    PUT = "PUT"
    DELETE = "DELETE"

class ResponseMessages:
    MISSING_REQUIRED_FIELDS = "Missing required fields"
    DOCUMENT_UPDATED_SUCCESSFULLY = "Document updated successfully"
    USER_ALREADY_EXISTS = "User already exists"
    USER_REGISTERED_SUCCESSFULLY = "User registered successfully"
    UNKNOWN = "Unknown"
    DOCUMENT_UPLOADED_SUCCESSFULLY = "Document uploaded successfully"
    INVALID_EMAIL_OR_PASSWORD = "Invalid email or password"
    DOCUMENT_NOT_FOUND = "Document not found"
    DOCUMENT_DELETED_SUCCESSFULLY = "Document deleted successfully"
    SIGN_UP_MESSAGE = "You have signed up successfully"
    EMAIL_OR_PASSWORD_MISSING = "Either the email or password field is missing."