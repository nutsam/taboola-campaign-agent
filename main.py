"""
This project is now a FastAPI application.
The previous command-line demonstrations have been deprecated.

To run the application:

1. Install the required dependencies:
   pip install -r requirements.txt

2. Start the server using uvicorn:
   uvicorn app:app --reload

3. Once the server is running, you can access the API at http://127.0.0.1:8000

   - Interactive API documentation (Swagger UI) is available at http://127.0.0.1:8000/docs
   - You can send POST requests to the /v1/chat and /v1/migrate endpoints from there.
"""

if __name__ == "__main__":
    print(__doc__)