from flask import Flask, request, jsonify, render_template
from groq import Groq
import MySQLdb
from MySQLdb.cursors import DictCursor  # Import DictCursor

app = Flask(__name__)

# Groq API setup
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

# MySQL Database connection
def get_db_connection():
    return MySQLdb.connect(
        host="localhost",  # Your MySQL host
        user="root",       # Your MySQL username
        password="adrian999",  # Your MySQL password
        database="shelfsearch",  # Your MySQL database name
        cursorclass=DictCursor  # Use DictCursor here
    )

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/summarize", methods=["POST"])
def summarize():
    data = request.json
    book_title = data.get("book_title")
    
    if not book_title:
        return jsonify({"error": "Book title is required"}), 400
    
    # Split title and author (assuming the format is "Book Title by Author")
    try:
        title, author = book_title.split(" by ")
    except ValueError:
        return jsonify({"error": "Please enter the book title in the format 'Title by Author'"}), 400
    
    # Check if the book exists in the database
    connection = get_db_connection()
    cursor = connection.cursor()  # No need for dictionary=True, DictCursor is used
    cursor.execute("SELECT * FROM books WHERE title = %s AND author = %s", (title, author))
    book = cursor.fetchone()

    if not book:
        return jsonify({"error": "Book not found in the database"}), 404
    
    # If the book exists in the database, fetch the summary from Groq API
    try:
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a chatbot specialized in summarizing books. "
                        "Based on the information provided by the user, such as the book's title and author, "
                        "your task is to provide a concise and accurate summary of the book."
                    ),
                },
                {"role": "user", "content": book_title},
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        # Access the content of the first message
        response_text = completion.choices[0].message.content
        return jsonify({"summary": response_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        connection.close()

# New route to suggest books based on genre
@app.route("/suggest_books", methods=["GET"])
def suggest_books():
    genre = request.args.get("genre")
    
    if not genre:
        return jsonify({"error": "Genre is required"}), 400
    
    # Query the database for books of the given genre
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT title, author FROM books WHERE genre = %s", (genre,))
    books = cursor.fetchall()

    if not books:
        return jsonify({"error": f"No books found for genre: {genre}"}), 404

    # Return a list of books with the title and author
    book_list = [{"title": book["title"], "author": book["author"]} for book in books]
    return jsonify({"suggested_books": book_list})

@app.route("/check_availability", methods=["GET"])
def check_availability():
    # Get book title and author from query parameters
    book_title = request.args.get("book_title")
    book_author = request.args.get("author")
    
    if not book_title or not book_author:
        return jsonify({"error": "Both book title and author are required"}), 400

    # Query the database for the book
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "SELECT title, author, status, ShelfLocation FROM books WHERE title = %s AND author = %s",
            (book_title, book_author)
        )
        book = cursor.fetchone()

        if not book:
            return jsonify({"error": "Book not found in the database"}), 404

        # Check availability and return the result
        availability_status = "Available" if book["status"].lower() == "available" else "Borrowed"
        return jsonify({
            "title": book["title"],
            "author": book["author"],
            "availability": availability_status,
            "shelflocation": book["ShelfLocation"]
        })

    except MySQLdb.Error as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    finally:
        # Ensure the connection is always closed
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()


@app.route("/related_books", methods=["POST"])
def related_books():
    data = request.json
    user_question = data.get("question")

    if not user_question:
        return jsonify({"error": "Question is required"}), 400

    try:
        # Use Groq API to analyze the user's question and suggest related books
        groq_response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a chatbot that analyzes user questions to suggest related books. "
                        "Based on the input question, provide a some books that match the context or keywords."
                        "Make short explanation of it."
                    ),
                },
                {"role": "user", "content": user_question},
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        # Extract book suggestions from the Groq API response
        suggestions = groq_response.choices[0].message.content
        
        if not suggestions.strip():
            return jsonify({"message": "No related books found for your question"}), 404

        # Parse the suggestions into a structured format
        books = []
        for line in suggestions.split("\n"):
            if " by " in line:
                title, author = line.split(" by ", 1)
                books.append({"title": title.strip(), "author": author.strip()})

        # Return the list of books
        return jsonify({"related_books": books})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route("/ask_question", methods=["POST"]) 
def ask_question():
    data = request.json
    user_question = data.get("question")

    if not user_question:
        return jsonify({"error": "Question is required"}), 400

    try:
        # Use Groq API to analyze the user's question and generate a response
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Create a friendly and knowledgeable library assistant chatbot that can only help users answer questions about books, reading techniques or anything related to books."
                        " Ensure the interaction is clear, helpful, and tailored to the user's needs."
                        
                    ),
                },
                {"role": "user", "content": user_question},
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        # Extract the answer from the Groq response
        answer = completion.choices[0].message.content
        return jsonify({"answer": answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500 

if __name__ == "__main__":
    app.run(debug=True)