
# from database.db_connection import get_chalan_db_connection


# def get_violation_fine(violation_name):
#     connection = get_chalan_db_connection()
#     cursor = connection.cursor(dictionary=True)

#     query = """
#         SELECT *
#         FROM violation
#         WHERE LOWER(violation_name) = LOWER(%s)
#     """

#     cursor.execute(query, (violation_name,))

#     violation = cursor.fetchone()

#     cursor.close()
#     connection.close()

#     return violation

# def save_challan(
#     vehicle_reg,
#     owner_name,
#     vehicle_type,
#     violation_name,
#     fine
# ):
#     connection = get_chalan_db_connection()
#     cursor = connection.cursor()

#     query = """
#         INSERT INTO challan_records
#         (
#             vehicle_reg,
#             owner_name,
#             vehicle_type,
#             violation_name,
#             fine
#         )
#         VALUES (%s, %s, %s, %s, %s)
#     """

#     values = (
#         vehicle_reg,
#         owner_name,
#         vehicle_type,
#         violation_name,
#         fine
#     )

#     cursor.execute(query, values)

#     connection.commit()

#     cursor.close()
#     connection.close()



from database.db_connection import get_chalan_db_connection


# ============================================================
# GET VIOLATION FINE
# ============================================================

def get_violation_fine(violation_name):

    connection = get_chalan_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT *
        FROM chalan_db.violation
        WHERE LOWER(violation_name) = LOWER(%s)
    """

    cursor.execute(query, (violation_name,))

    violation = cursor.fetchone()

    cursor.close()
    connection.close()

    return violation


# ============================================================
# SAVE CHALLAN
# ============================================================

def save_challan(
    vehicle_reg,
    owner_name,
    vehicle_type,
    violation_name,
    fine
):

    connection = get_chalan_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO challan_records
        (
            vehicle_reg,
            owner_name,
            vehicle_type,
            violation_name,
            fine
        )
        VALUES (%s, %s, %s, %s, %s)
    """

    values = (
        vehicle_reg,
        owner_name,
        vehicle_type,
        violation_name,
        fine
    )

    cursor.execute(query, values)

    connection.commit()

    cursor.close()
    connection.close()

    return True