# Get number of documents in the database
def get_document_count(conn, cursor):

    try:
        if cursor:
            cursor.execute("SELECT COUNT(*) FROM document;")
            result = cursor.fetchone()
            if result:
                count = result[0]
                return count
            else:
                print("Error: Unable to fetch document count.")
                return 0
        else:
            print("Error: Unable to get database cursor.")
            return 0
    except Exception as e:
        print(f"Error getting document count: {e}")


