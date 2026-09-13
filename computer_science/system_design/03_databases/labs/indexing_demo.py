import psycopg2
import time
import random
import string

def get_random_string(length):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))

def run_demo():
    print("Connecting to Postgres...")
    # You must have docker-compose running for this to work!
    conn = psycopg2.connect(
        dbname="indexing_lab",
        user="db_admin",
        password="secretpassword",
        host="localhost",
        port="5432"
    )
    conn.autocommit = True
    cursor = conn.cursor()

    print("Creating table 'users'...")
    cursor.execute("""
        DROP TABLE IF EXISTS users;
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50),
            email VARCHAR(100),
            age INT
        );
    """)

    print("Inserting 100,000 rows (this will take a few seconds)...")
    # Batch insert for speed
    args_str = ','.join(
        cursor.mogrify("(%s, %s, %s)", (
            f"user_{i}", 
            f"user_{i}_{get_random_string(5)}@example.com", 
            random.randint(18, 80)
        )).decode('utf-8')
        for i in range(100000)
    )
    cursor.execute("INSERT INTO users (username, email, age) VALUES " + args_str)

    # Pick a random user to search for
    target_username = "user_75000"

    print("\n--- TEST 1: Searching WITHOUT an index ---")
    start = time.time()
    # EXPLAIN ANALYZE actually runs the query and returns execution stats
    cursor.execute(f"EXPLAIN ANALYZE SELECT * FROM users WHERE username = '{target_username}';")
    explain_no_index = cursor.fetchall()
    duration_no_index = time.time() - start
    
    for row in explain_no_index:
        print(row[0])
    print(f"Time taken (Python side): {duration_no_index:.4f} seconds")


    print("\n--- Creating B-Tree Index on username ---")
    cursor.execute("CREATE INDEX idx_username ON users(username);")


    print("\n--- TEST 2: Searching WITH an index ---")
    start = time.time()
    cursor.execute(f"EXPLAIN ANALYZE SELECT * FROM users WHERE username = '{target_username}';")
    explain_with_index = cursor.fetchall()
    duration_with_index = time.time() - start
    
    for row in explain_with_index:
        print(row[0])
    print(f"Time taken (Python side): {duration_with_index:.4f} seconds")

    print("\nNotice the difference in the query plan!")
    print("Without index: 'Seq Scan' (Sequential Scan - checks every row)")
    print("With index: 'Index Scan' (Uses the B-Tree to find the row instantly)")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    try:
        run_demo()
    except Exception as e:
        print(f"Error: {e}")
        print("Did you remember to run 'docker-compose up -d' first? You need 'psycopg2' installed too.")
