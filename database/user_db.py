
from database.db_connection import get_user_db_connection


def add_user(user_name, vehicle_reg, vehicle_type, mobile_number):
    connection = get_user_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO users
        (user_name, vehicle_reg, vehicle_type, mobile_number)
        VALUES (%s, %s, %s, %s)
    """

    values = (
        user_name,
        vehicle_reg,
        vehicle_type,
        mobile_number
    )

    cursor.execute(query, values)
    connection.commit()

    cursor.close()
    connection.close()

    print("User added successfully.")


def get_user(vehicle_reg):
    connection = get_user_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT *
        FROM users
        WHERE vehicle_reg = %s
    """

    cursor.execute(query, (vehicle_reg,))

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    return user

