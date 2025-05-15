import os
import threading

DATA_DIR = "data"

class TableMetadata:
    def __init__(self, primary_key, unique_keys):
        self.primary_key = primary_key
        self.unique_keys = set(unique_keys)

class TableManager:
    def __init__(self):
        if not os.path.exists(DATA_DIR):
            os.mkdir(DATA_DIR)
        self.table_data = {}
        self.table_metadata = {}
        self.table_locks = {}
        self.metadata_lock = threading.Lock()

    def begin_transaction(self, tables, is_read_only):
        from transaction import Transaction
        return Transaction(self, tables, is_read_only)

    def create_table(self, table_name, columns, primary_key, unique_keys):
        with self.metadata_lock:
            file_path = os.path.join(DATA_DIR, f"{table_name}.txt")
            if os.path.exists(file_path):
                print("Table already exists.")
                return
            if primary_key not in columns:
                raise ValueError(f"Primary key '{primary_key}' must be a table column.")
            for key in unique_keys:
                if key not in columns:
                    raise ValueError(f"Unique key '{key}' must be a table column.")
            with open(file_path, "w") as f:
                f.write(",".join(columns) + "\n")
            self.table_data[table_name] = {col: [] for col in columns}
            meta = TableMetadata(primary_key, unique_keys)
            self.table_metadata[table_name] = meta
            self._save_metadata(table_name, meta)
            print(f"Table '{table_name}' created.")

    def drop_table(self, table_name):
        with self.metadata_lock:
            file_path = os.path.join(DATA_DIR, f"{table_name}.txt")
            meta_path = os.path.join(DATA_DIR, f"{table_name}.meta.txt")
            if os.path.exists(file_path):
                os.remove(file_path)
                if os.path.exists(meta_path):
                    os.remove(meta_path)
                self.table_data.pop(table_name, None)
                self.table_metadata.pop(table_name, None)
                self.table_locks.pop(table_name, None)
                print(f"Table '{table_name}' deleted.")
            else:
                print("Table not found or could not delete.")

    def show_tables(self):
        tables = [f[:-4] for f in os.listdir(DATA_DIR) if f.endswith(".txt") and not f.endswith(".meta.txt")]
        if not tables:
            print("No tables found.")
        else:
            print("Tables:")
            for t in tables:
                print(f"- {t}")

    def get_table_lock(self, table):
        if table not in self.table_locks:
            self.table_locks[table] = threading.RLock()
        return self.table_locks[table]

    def get_table_metadata(self, table_name):
        if table_name not in self.table_metadata:
            self._load_metadata(table_name)
        return self.table_metadata[table_name]

    def _save_metadata(self, table_name, meta):
        meta_path = os.path.join(DATA_DIR, f"{table_name}.meta.txt")
        with open(meta_path, "w") as f:
            f.write(f"PRIMARY_KEY={meta.primary_key}\n")
            if meta.unique_keys:
                f.write(f"UNIQUE_KEYS={','.join(meta.unique_keys)}\n")

    def _load_metadata(self, table_name):
        meta_path = os.path.join(DATA_DIR, f"{table_name}.meta.txt")
        primary_key = None
        unique_keys = set()
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                for line in f:
                    if line.startswith("PRIMARY_KEY="):
                        primary_key = line.strip().split("=")[1]
                    elif line.startswith("UNIQUE_KEYS="):
                        unique_keys.update(line.strip().split("=")[1].split(","))
        self.table_metadata[table_name] = TableMetadata(primary_key, unique_keys)
    
    def describe_table(self, table_name):
        if table_name not in self.table_data:
            self._load_table_to_memory(table_name)
        metadata = self.get_table_metadata(table_name)
        data = self.table_data.get(table_name)
        if not data:
            print("Table not found.")
            return
        print(f"Table: {table_name}")
        print("Columns:")
        for col in data.keys():
            flags = []
            if col == metadata.primary_key:
                flags.append("PRIMARY KEY")
            if col in metadata.unique_keys:
                flags.append("UNIQUE")
            print(f" - {col} {' '.join(flags)}")

    def alter_add_column(self, table_name, column_name):
        self._load_table_to_memory(table_name)
        if column_name in self.table_data[table_name]:
            print(f"Column '{column_name}' already exists.")
            return
        self.table_data[table_name][column_name] = [""] * len(next(iter(self.table_data[table_name].values())))
        self._persist_table(table_name)
        print(f"Column '{column_name}' added to '{table_name}'.")


    def alter_drop_column(self, table_name, column_name):
        self._load_table_to_memory(table_name)
        if column_name not in self.table_data[table_name]:
            print(f"Column '{column_name}' does not exist.")
            return
        if column_name == self.table_metadata[table_name].primary_key:
            print("Cannot drop PRIMARY KEY column.")
            return
        del self.table_data[table_name][column_name]
        self.table_metadata[table_name].unique_keys.discard(column_name)
        self._persist_table(table_name)
        self._save_metadata(table_name, self.table_metadata[table_name])
        print(f"Column '{column_name}' dropped from '{table_name}'.")


    def alter_rename_column(self, table_name, old_name, new_name):
        self._load_table_to_memory(table_name)
        if old_name not in self.table_data[table_name]:
            print(f"Column '{old_name}' does not exist.")
            return
        if new_name in self.table_data[table_name]:
            print(f"Column '{new_name}' already exists.")
            return
        self.table_data[table_name][new_name] = self.table_data[table_name].pop(old_name)
        meta = self.table_metadata[table_name]
        if old_name == meta.primary_key:
            meta.primary_key = new_name
        if old_name in meta.unique_keys:
            meta.unique_keys.remove(old_name)
            meta.unique_keys.add(new_name)
        self._persist_table(table_name)
        self._save_metadata(table_name, meta)
        print(f"Column '{old_name}' renamed to '{new_name}' in '{table_name}'.")
        
    
    def _persist_table(self, table_name):
        file_path = os.path.join(DATA_DIR, f"{table_name}.txt")
        data = self.table_data[table_name]
        with open(file_path, "w") as f:
            headers = list(data.keys())
            f.write(",".join(headers) + "\n")
            rows = zip(*[data[col] for col in headers])
            for row in rows:
                f.write(",".join(row) + "\n")



    def _load_table_to_memory(self, table_name):
        file_path = os.path.join(DATA_DIR, f"{table_name}.txt")
        if not os.path.exists(file_path): return
        with open(file_path, "r") as f:
            lines = f.readlines()
        if not lines: return
        columns = lines[0].strip().split(",")
        self.table_data[table_name] = {col: [] for col in columns}

