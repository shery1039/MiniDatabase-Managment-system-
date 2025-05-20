import os
import threading
import copy

class Transaction:
    def __init__(self, tm, tables, is_read_only):
        self.tm = tm
        self.tables = sorted(tables)
        self.is_read_only = is_read_only
        self.locks = []
        self.data = {}

        for table in self.tables:
            lock = tm.get_table_lock(table)
            lock.acquire()
            self.locks.append(lock)
            self._load_table(table)

    def _load_table(self, table):
        file_path = os.path.join("data", f"{table}.txt")
        if not os.path.exists(file_path):
            return
        with open(file_path, "r") as f:
            lines = f.readlines()
        columns = lines[0].strip().split(",")
        data = {col: [] for col in columns}
        for line in lines[1:]:
            values = line.strip().split(",")
            for i, col in enumerate(columns):
                data[col].append(values[i] if i < len(values) else "")
        if self.is_read_only:
            self.tm.table_data[table] = data
        else:
            self.data[table] = copy.deepcopy(data)

    def insert_row(self, table, values):
        if self.is_read_only:
            raise Exception("Cannot write in read-only transaction")
        table_data = self.data[table]
        columns = list(table_data.keys())
        if len(values) != len(columns):
            raise ValueError("Value count doesn't match column count.")
        meta = self.tm.get_table_metadata(table)
        for idx, col in enumerate(columns):
            val = values[idx]
            if col == meta.primary_key or col in meta.unique_keys:
                if val in table_data[col]:
                    raise ValueError(f"Duplicate value '{val}' in column '{col}'")
        for idx, col in enumerate(columns):
            table_data[col].append(values[idx])
        print(f"Row inserted into '{table}'.")

    def read_table(self, table, selected_columns=None, order_by=None, limit=None):
        data = self.tm.table_data.get(table) if self.is_read_only else self.data.get(table)
        if not data:
            print("Table does not exist.")
            return
        headers = selected_columns if selected_columns else list(data.keys())
        rows = list(zip(*[data[h] for h in headers]))

        if order_by and order_by in data:
            order_idx = headers.index(order_by) if selected_columns else list(data.keys()).index(order_by)
            rows.sort(key=lambda x: x[order_idx])

        if limit is not None:
            rows = rows[:limit]

        print(",".join(headers))
        for row in rows:
            print(",".join(row))

    def read_table_with_condition(self, table, column, value, selected_columns=None, order_by=None, limit=None):
        data = self.tm.table_data.get(table) if self.is_read_only else self.data.get(table)
        if not data:
            print("Table does not exist.")
            return
        if column not in data:
            print(f"WHERE column '{column}' does not exist.")
            return

        headers = selected_columns if selected_columns else list(data.keys())
        for h in headers:
            if h not in data:
                print(f"Selected column '{h}' does not exist.")
                return
        if order_by and order_by not in data:
            print(f"ORDER BY column '{order_by}' does not exist.")
            return

        matching_rows = []
        for i in range(len(data[column])):
            if data[column][i] == value:
                matching_rows.append(tuple(data[h][i] for h in headers))


        if order_by:
            order_idx = headers.index(order_by)
            matching_rows.sort(key=lambda x: x[order_idx])

        if limit is not None:
            matching_rows = matching_rows[:limit]

        print(",".join(headers))
        for row in matching_rows:
            print(",".join(row))

    def update_rows(self, table, set_col, new_val, where_col, where_val):
        if self.is_read_only:
            raise Exception("Cannot write in read-only transaction")
        data = self.data[table]
        count = 0
        for i in range(len(data[where_col])):
            if data[where_col][i] == where_val:
                data[set_col][i] = new_val
                count += 1
        print(f"Updated {count} row(s).")

    def delete_rows(self, table, column, value):
        if self.is_read_only:
            raise Exception("Cannot write in read-only transaction")
        data = self.data[table]
        indices = [i for i, val in enumerate(data[column]) if val == value]
        for col in data:
            for i in reversed(indices):
                del data[col][i]
        print(f"Deleted {len(indices)} row(s).")

    def commit(self):
        if not self.is_read_only:
            for table in self.tables:
                file_path = os.path.join("data", f"{table}.txt")
                data = self.data[table]
                with open(file_path, "w") as f:
                    headers = list(data.keys())
                    f.write(",".join(headers) + "\n")
                    for i in range(len(data[headers[0]])):
                        row = ",".join(data[h][i] for h in headers)
                        f.write(row + "\n")
                self.tm.table_data[table] = data
        self._release_locks()

    def _release_locks(self):
        for lock in self.locks:
            lock.release()
        self.locks.clear()
