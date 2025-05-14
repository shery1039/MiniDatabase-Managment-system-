# MiniDatabase-Managment-system-
# 🛠️ Python Database CLI Project

A mini command-line database system built from scratch in Python. It simulates SQL-like operations using in-memory data structures and flat file storage — ideal for learning how databases work under the hood.

---

## 🚀 Features

- ✅ Create and drop tables
- ✅ Insert, update, delete rows
- ✅ SELECT with `WHERE` clause
- ✅ Table schema inspection with `DESCRIBE`
- ✅ Table structure modification using `ALTER TABLE`
- ✅ Row sorting and limiting (Coming Soon)
- ✅ Export table data to CSV and JSON (Coming Soon)
- ✅ Primary Key & Unique constraint enforcement
- ✅ Transactional operations with basic locking

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

