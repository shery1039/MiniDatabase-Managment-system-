from table_manager import TableManager
from transaction import Transaction

class DatabaseCLI:
    def __init__(self):
        self.tm = TableManager()

    def start(self):
        while True:
            command = input("db> ").strip()
            if command.upper() == "EXIT":
                print("Exiting database CLI.")
                break
            try:
                self.execute_command(command)
            except Exception as e:
                print(f"Error: {e}")

    def execute_command(self, command):
        upper_command = command.upper()

        if upper_command.startswith("CREATE TABLE"):
            self._handle_create_table(command)

        elif upper_command.startswith("INSERT INTO"):
            self._handle_insert(command)

        elif upper_command.startswith("SELECT"):
            self._handle_select(command)

        elif upper_command.startswith("UPDATE"):
            self._handle_update(command)

        elif upper_command.startswith("DELETE FROM"):
            self._handle_delete(command)

        elif upper_command.startswith("DROP TABLE"):
            table_name = command[len("DROP TABLE "):].strip()
            self.tm.drop_table(table_name)

        elif upper_command == "SHOW TABLES":
            self.tm.show_tables()

        elif upper_command.startswith("DESCRIBE"):
            table_name = command[len("DESCRIBE "):].strip()
            self.tm.describe_table(table_name)

        elif upper_command.startswith("ALTER TABLE"):
            self._handle_alter_table(command)

        else:
            print("Unknown command.")

    def _handle_create_table(self, command):
        table_start = len("CREATE TABLE ")
        paren_start = command.index("(")
        table_name = command[table_start:paren_start].strip()
        paren_end = command.rindex(")")
        spec_str = command[paren_start + 1:paren_end]

        columns = []
        primary_key = None
        unique_keys = set()

        for spec in spec_str.split(","):
            spec = spec.strip()
            if spec.upper().startswith("PRIMARY KEY"):
                primary_key = spec[len("PRIMARY KEY"):].strip().replace("(", "").replace(")", "")
            elif spec.upper().startswith("UNIQUE"):
                key = spec[len("UNIQUE"):].strip().replace("(", "").replace(")", "")
                unique_keys.add(key)
            else:
                columns.append(spec)

        if not primary_key:
            raise ValueError("A PRIMARY KEY must be specified for table creation.")

        self.tm.create_table(table_name, columns, primary_key, unique_keys)

    def _handle_insert(self, command):
        into_index = command.upper().index("INTO") + 5
        values_index = command.upper().index("VALUES")
        table_name = command[into_index:values_index].strip()
        values_str = command[values_index + 6:].strip()
        values = self.parse_values(values_str)

        tx = self.tm.begin_transaction([table_name], False)
        tx.insert_row(table_name, values)
        tx.commit()

    def _handle_select(self, command):
        command_upper = command.upper()

        # Step 1: Break command into SELECT, FROM and remaining parts
        select_index = command_upper.index("SELECT") + len("SELECT")
        from_index = command_upper.index("FROM")
        select_clause = command[select_index:from_index].strip()
        columns = None if select_clause.strip() == "*" else [col.strip() for col in select_clause.split(",")]

        # Initial parse for FROM clause
        rest = command[from_index + len("FROM"):].strip()

        # Initialize parts
        table_name = None
        where_clause = None
        order_by = None
        limit = None

        # Helper to extract optional parts safely
        def extract_clause(text, keyword):
            idx = text.upper().find(keyword)
            return (text[idx + len(keyword):].strip(), text[:idx].strip()) if idx != -1 else (None, text)

        # Step 2: Parse optional LIMIT
        limit_part, rest = extract_clause(rest, "LIMIT")
        if limit_part:
            limit = int(limit_part.split()[0])

    # Step 3: Parse optional ORDER BY
        order_part, rest = extract_clause(rest, "ORDER BY")
        if order_part:
            order_by = order_part.split()[0].strip()

        # Step 4: Parse optional WHERE
        where_part, rest = extract_clause(rest, "WHERE")
        if where_part:
            where_clause = self.parse_condition(where_part.strip())

        # Remaining is the table name
        table_name = rest.strip()

        # Execute transaction
        tx = self.tm.begin_transaction([table_name], True)
        if where_clause:
            tx.read_table_with_condition(table_name, *where_clause, columns, order_by, limit)
        else:
            tx.read_table(table_name, columns, order_by, limit)
        tx.commit()


    def _handle_update(self, command):
        table_name = command[len("UPDATE "):command.upper().index("SET")].strip()
        set_str = command[command.upper().index("SET") + 4:command.upper().index("WHERE")].strip()
        where_str = command[command.upper().index("WHERE") + 6:].strip()

        set_col, new_val = self.parse_condition(set_str)
        where_col, where_val = self.parse_condition(where_str)

        tx = self.tm.begin_transaction([table_name], False)
        tx.update_rows(table_name, set_col, new_val, where_col, where_val)
        tx.commit()

    def _handle_delete(self, command):
        table_name = command[len("DELETE FROM "):command.upper().index("WHERE")].strip()
        column, value = self.parse_condition(command[command.upper().index("WHERE") + 6:].strip())

        tx = self.tm.begin_transaction([table_name], False)
        tx.delete_rows(table_name, column, value)
        tx.commit()

    def _handle_alter_table(self, command):
        parts = command.split()
        table_name = parts[2]
        sub_command = " ".join(parts[3:]).strip().upper()

        if sub_command.startswith("ADD COLUMN"):
            column_name = command.upper().split("ADD COLUMN", 1)[1].strip()
            self.tm.alter_add_column(table_name, column_name)

        elif sub_command.startswith("DROP COLUMN"):
            column_name = command.upper().split("DROP COLUMN", 1)[1].strip()
            self.tm.alter_drop_column(table_name, column_name)

        elif sub_command.startswith("RENAME COLUMN"):
            _, old, _, new = command.upper().split()[3:7]
            self.tm.alter_rename_column(table_name, old, new)

        else:
            print("Unsupported ALTER TABLE command.")

    def parse_values(self, values_str):
        values_str = values_str.strip("()")
        parts = []
        val = ""
        in_quote = False

        for ch in values_str:
            if ch == "'" and not in_quote:
                in_quote = True
            elif ch == "'" and in_quote:
                in_quote = False
            elif ch == "," and not in_quote:
                parts.append(val.strip().strip("'"))
                val = ""
            else:
                val += ch

        if val:
            parts.append(val.strip().strip("'"))

        return parts

    def parse_condition(self, cond_str):
        col, val = cond_str.split("=", 1)
        return col.strip(), val.strip().strip("'").strip()

