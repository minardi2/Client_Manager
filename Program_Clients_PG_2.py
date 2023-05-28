import psycopg2

# Параметры подключения к базе данных PostgreSQL
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'your_database_name'
DB_USER = 'your_username'
DB_PASSWORD = 'your_password'


class DatabaseManager:
    def __init__(self):
        self.conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)

    def __enter__(self):
        return self.conn.cursor()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()


def create_tables():
    """Создание структуры базы данных"""
    with DatabaseManager() as cursor:
        # Создание таблицы "clients" для хранения информации о клиентах
        create_clients_table_query = '''
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                email VARCHAR(100)
            );
        '''
        cursor.execute(create_clients_table_query)

        # Создание таблицы "phones" для хранения информации о телефонах клиентов
        create_phones_table_query = '''
            CREATE TABLE IF NOT EXISTS phones (
                id SERIAL PRIMARY KEY,
                client_id INT,
                phone_number VARCHAR(20),
                FOREIGN KEY (client_id) REFERENCES clients (id) ON DELETE CASCADE
            );
        '''
        cursor.execute(create_phones_table_query)


def add_client(first_name, last_name, email):
    """Добавление нового клиента в базу данных"""
    with DatabaseManager() as cursor:
        insert_client_query = '''
            INSERT INTO clients (first_name, last_name, email)
            VALUES (%s, %s, %s)
            RETURNING id;
        '''
        cursor.execute(insert_client_query, (first_name, last_name, email))
        client_id = cursor.fetchone()[0]

    return client_id


def add_phone(client_id, phone_number):
    """Добавление телефона для существующего клиента"""
    with DatabaseManager() as cursor:
        insert_phone_query = '''
            INSERT INTO phones (client_id, phone_number)
            VALUES (%s, %s);
        '''
        cursor.execute(insert_phone_query, (client_id, phone_number))


def update_client(client_id, **kwargs):
    """Изменение данных о клиенте"""
    with DatabaseManager() as cursor:
        update_client_query = '''
            UPDATE clients
            SET {0}
            WHERE id = %s;
        '''
        set_columns = ', '.join(f"{key} = %s" for key in kwargs.keys())
        update_client_query = update_client_query.format(set_columns)
        cursor.execute(update_client_query, tuple(kwargs.values()) + (client_id,))


def remove_client(client_id):
    """Удаление существующего клиента"""
    with DatabaseManager() as cursor:
        delete_client_query = '''
            DELETE FROM clients
            WHERE id = %s;
        '''
        cursor.execute(delete_client_query, (client_id,))


def remove_phone(client_id, phone_number):
    """Удаление телефона для существующего клиента"""
    with DatabaseManager() as cursor:
        delete_phone_query = '''
            DELETE FROM phones
            WHERE client_id = %s AND phone_number = %s;
        '''
        cursor.execute(delete_phone_query, (client_id, phone_number))


def search_clients(first_name=None, last_name=None, email=None, phone_number=None):
    """Поиск клиентов по имени, фамилии, email или телефону"""
    with DatabaseManager() as cursor:
        search_query = '''
            SELECT DISTINCT clients.id, first_name, last_name, email, phone_number
            FROM clients
            LEFT JOIN phones ON clients.id = phones.client_id
            WHERE {0};
        '''

        conditions = []
        parameters = []

        if first_name:
            conditions.append("first_name ILIKE %s")
            parameters.append(f"%{first_name}%")
        if last_name:
            conditions.append("last_name ILIKE %s")
            parameters.append(f"%{last_name}%")
        if email:
            conditions.append("email ILIKE %s")
            parameters.append(f"%{email}%")
        if phone_number:
            conditions.append("phone_number ILIKE %s")
            parameters.append(f"%{phone_number}%")

        where_clause = " OR ".join(conditions)
        search_query = search_query.format(where_clause)

        cursor.execute(search_query, tuple(parameters))
        results = cursor.fetchall()

        clients = []
        for row in results:
            client_id, first_name, last_name, email, phone_number = row
            client = {
                'id': client_id,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone_number': phone_number
            }
            clients.append(client)

    return clients


if __name__ == "__main__":
    # Создание структуры базы данных
    create_tables()

    # Добавление нового клиента
    client_id = add_client('Bruce', 'Mclaren', 'brucemclaren@mail.com')
    print(f"Added client with ID: {client_id}")

    # Добавление телефонов для клиента
    add_phone(client_id, '123456789')
    add_phone(client_id, '987654321')

    # Изменение данных о клиенте
    update_client(client_id, first_name='Will', last_name='Smith', email='willsmith@mail.com')

    # Удаление телефона для клиента
    remove_phone(client_id, '987654321')

    # Удаление клиента
    remove_client(client_id)

    # Поиск клиентов по параметрам
    search_results = search_clients(first_name='Bruce', email='brucemclaren@mail.com')
    for client in search_results:
        print(client)
