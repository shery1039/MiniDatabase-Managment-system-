# MiniDatabase-Managment-system-
# 🛠️ Python Database CLI Project

A mini command-line database system built from scratch in Python. It simulates SQL-like operations using in-memory data structures and flat file storage — ideal for learning how databases work under the hood.

---

## 🚀 Features

🚀 Features
✅ Core SQL-Like Operations:

CREATE TABLE, DROP TABLE

INSERT INTO, UPDATE, DELETE FROM

SELECT with WHERE, ORDER BY, and LIMIT

✅ Schema & Metadata:

DESCRIBE to inspect table schema

ALTER TABLE to:

Add/Drop columns

Rename columns

Enforces PRIMARY KEY and UNIQUE constraints

✅ Transactions & Locking:

Transaction handling with file-based commit

Read-only and write-safe operations

Thread-safe table access using threading.RLock

✅ Storage:

Flat file structure (data/ folder)

Auto-generated .txt files for each table

Metadata saved in .meta.txt files

✅ CLI Interface:

Interactive command-line with db> prompt

Graceful error messages and validation
---

## 🧱 Project Structure

project/
├── main.py # CLI entry point
├── database_cli.py # SQL-like command parser
├── table_manager.py # Manages tables and schema
├── transaction.py # Handles read/write operations
└── data/ # Flat file storage for tables
├── users.txt
└── users.meta.txt

🧪 Supported SQL Commands

🔧 Table Management

CREATE TABLE students (id, name, age, PRIMARY KEY(id), UNIQUE(name))
DROP TABLE students
DESCRIBE students
SHOW TABLES

 Data Manipulation

INSERT INTO students VALUES ('1', 'Alice', '22')
UPDATE students SET age='23' WHERE name='Alice'
DELETE FROM students WHERE id='1'


🔍 Querying

SELECT * FROM students
SELECT id, name FROM students WHERE age='20'
SELECT * FROM students ORDER BY name
SELECT * FROM students WHERE age='22' ORDER BY id LIMIT 3

🔁 Schema Modification

ALTER TABLE students ADD COLUMN email
ALTER TABLE students DROP COLUMN email
ALTER TABLE students RENAME COLUMN name TO fullname

🧠 Upcoming Features
 EXPORT TO CSV and EXPORT TO JSON

 NOT NULL and DEFAULT constraints

 JOIN operations

 Advanced filtering (AND, OR, comparison operators)

 Django Web Interface

🌐 Django Integration (In Progress)
This project is being extended into a Django web app with:

A REST API endpoint to run queries

HTML UI for visual database interaction

JSON-based query execution and response

▶️ Running the CLI

python main.py
You’ll see:
db>
Then enter any supported SQL-like command!

📂 Example Session

CREATE TABLE students (id, name, age, PRIMARY KEY(id), UNIQUE(name))
INSERT INTO students VALUES ('1', 'Alice', '22')
INSERT INTO students VALUES ('2', 'Bob', '20')
SELECT id, name FROM students WHERE age='20' ORDER BY id LIMIT 2
Output:

id,name
2,Bob

🙌 Contributing
This project is meant for educational exploration. If you'd like to contribute with new features, tests, or enhancements — feel free to fork and submit pull requests!