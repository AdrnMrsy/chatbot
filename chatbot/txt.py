from flask import Flask, request, jsonify,render_template
from groq import Groq
import MySQLdb
from MySQLdb.cursors import DictCursor

app = Flask(__name__)

# Groq API setup
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

# MySQL Database connection
def get_db_connection():
    return MySQLdb.connect(
        host="localhost",
        user="root",
        password="adrian999",
        database="shelfsearch",
        cursorclass=DictCursor
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
        # Use Groq API to analyze the user's question
        completion = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": (
                    "You are an expert database assistant. The database has a table named 'Books' with the following columns:\n"
                    "BookID (INT, primary key), Title (VARCHAR), Author (VARCHAR), Genre (VARCHAR), "
                    "PublicationYear (VARCHAR), Synopsis (TEXT), Status (ENUM with 'Available' or 'Borrowed'), "
                    "ShelfLocation (VARCHAR), and Barcode (VARCHAR, unique). Generate valid SQL queries based on this schema. "
                    "Do not include explanations, prefixes like 'sql', or markdown formatting."
                )},
                {"role": "user", "content": f"Translate the following question into a valid SQL query: {user_question}"},
            ],
            temperature=0.7,
            max_tokens=256,
            top_p=1.0
        )

        # Extract the generated SQL query and sanitize it
        generated_sql = completion.choices[0].message.content.strip()

        # Remove any markdown or unnecessary prefixes
        if "```" in generated_sql:
            generated_sql = generated_sql.split("```")[1].strip()  # Extract SQL code
        generated_sql = generated_sql.replace("sql\n", "").strip()  # Remove 'sql\n' if present

        # Connect to the database
        db_connection = get_db_connection()
        cursor = db_connection.cursor()

        # Execute the query securely
        cursor.execute(generated_sql)
        results = cursor.fetchall()

        # Close the database connection
        cursor.close()
        db_connection.close()

        return jsonify({"query": generated_sql, "results": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
