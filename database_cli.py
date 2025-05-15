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
            table_start = len("CREATE TABLE ")
            paren_start = command.index("(")
            table_name = command[table_start:paren_start].strip()
            paren_end = command.rindex(")")
            spec_str = command[paren_start + 1:paren_end]
            columns, primary_key, unique_keys = [], None, set()
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

        elif upper_command.startswith("INSERT INTO"):
            into_index = upper_command.index("INTO") + 5
            values_index = upper_command.index("VALUES")
            table_name = command[into_index:values_index].strip()
            values_str = command[values_index + 6:].strip()
            values = self.parse_values(values_str)
            tx = self.tm.begin_transaction([table_name], False)
            tx.insert_row(table_name, values)
            tx.commit()

        elif upper_command.startswith("SELECT * FROM"):
            from_index = upper_command.index("FROM") + 5
            parts = command[from_index:].strip().split("WHERE")
            table_name = parts[0].strip()
            tx = self.tm.begin_transaction([table_name], True)
            if len(parts) == 1:
                tx.read_table(table_name)
            else:
                column, value = self.parse_condition(parts[1].strip())
                tx.read_table_with_condition(table_name, column, value)
            tx.commit()

        elif upper_command.startswith("UPDATE"):
            table_name = command[len("UPDATE "):upper_command.index("SET")].strip()
            set_str = command[upper_command.index("SET") + 4:upper_command.index("WHERE")].strip()
            where_str = command[upper_command.index("WHERE") + 6:].strip()
            set_col, new_val = self.parse_condition(set_str)
            where_col, where_val = self.parse_condition(where_str)
            tx = self.tm.begin_transaction([table_name], False)
            tx.update_rows(table_name, set_col, new_val, where_col, where_val)
            tx.commit()

        elif upper_command.startswith("DELETE FROM"):
            table_name = command[len("DELETE FROM "):upper_command.index("WHERE")].strip()
            column, value = self.parse_condition(command[upper_command.index("WHERE") + 6:].strip())
            tx = self.tm.begin_transaction([table_name], False)
            tx.delete_rows(table_name, column, value)
            tx.commit()

        elif upper_command.startswith("DROP TABLE"):
            table_name = command[len("DROP TABLE "):].strip()
            self.tm.drop_table(table_name)

        elif upper_command == "SHOW TABLES":
            self.tm.show_tables()

        elif upper_command.startswith("DESCRIBE"):
            table_name = command[len("DESCRIBE "):].strip()
            self.tm.describe_table(table_name)

        elif upper_command.startswith("ALTER TABLE"):
            parts = command.split()
            table_name = parts[2]
            sub_command = " ".join(parts[3:]).strip()

            if sub_command.upper().startswith("ADD COLUMN"):
                column_name = sub_command[len("ADD COLUMN"):].strip()
                self.tm.alter_add_column(table_name, column_name)

            elif sub_command.upper().startswith("DROP COLUMN"):
                column_name = sub_command[len("DROP COLUMN"):].strip()
                self.tm.alter_drop_column(table_name, column_name)

            elif sub_command.upper().startswith("RENAME COLUMN"):
                _, old, _, new = sub_command.split()
                self.tm.alter_rename_column(table_name, old, new)

            else:
                print("Unsupported ALTER TABLE command.")

        else:
            print("Unknown command.")

    def parse_values(self, values_str):
        values_str = values_str.strip("()")
        parts, val, in_quote = [], "", False
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
        return col.strip(), val.strip().strip("'")