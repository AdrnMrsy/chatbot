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
        database="shelf",  # Your MySQL database name
        cursorclass=DictCursor  # Use DictCursor here
    )


@app.route("/")
def home():
    return render_template("index.html")
@app.route("/ask_question", methods=["POST"])
def ask_question():
    data = request.json
    user_question = data.get("question")

    if not user_question:
        return jsonify({"error": "Question is required"}), 400

    try:
        # Check if the user's question matches local data from the database
        

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM books")  # Execute SQL query
        books_data = cursor.fetchall()
        library_books = "\n".join(
    [
        f"{book['Title']}, {book['Author']}, "
        f"{book['Genre']}, {book['PublicationYear']}, "
        f"{book['Synopsis']}, {book['Status']}, "
        f"{book['ShelfLocation']}, {book['Barcode']}"
        for book in books_data
    ]   
)
        print(library_books)

        system_message_content = (
    "You are a library management system assistant. Use the provided book summaries as your sole source of information. "
    "Answer user questions accurately and helpfully based on the content of these summaries. Do not reference being an AI "
    "or any limitations—respond as if you are knowledgeable about the books in the library. "
    "If the book is not in the book data, do not provide a fabricated or non-existent answer stating that the book is available."
    f"Here is the book data:\n{library_books}"
)


        # Query library data from the database
        cursor.execute("SELECT question, value FROM library_info")
        library_data = cursor.fetchall()

        # Close the database connection
        cursor.close()
        connection.close()

        # Check if the user's question matches any of the library data
        for row in library_data:
            if row['question'] in user_question.lower():
                return jsonify({"answer": row['value']})

        # Use the AI model to process the question if no local match is found
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[ 
                {
                    "role": "system",
                    "content": system_message_content,
                },
                {"role": "user", "content": user_question},
            ],
            temperature=1,
            max_tokens=32768,
            top_p=1,
            stream=False,
            stop=None,
        )

        # Extract the answer from the Groq response
        ai_answer = completion.choices[0].message.content

        # If the AI's answer contains multiple points, it will include '\n' for newlines
        if ai_answer:
            return jsonify({"answer": ai_answer.strip()})

        return jsonify({"answer": ai_answer})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
if __name__ == "__main__":
    app.run(debug=True)