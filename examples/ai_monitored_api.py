"""Example: Code with expensive patterns that deburger catches."""

import boto3


# Bad: N+1 query pattern
async def get_order_details(order_ids):
    results = []
    for order_id in order_ids:
        order = db.query(order_id)  # deburger catches this
        results.append(order)
    return results


# Bad: Sequential async calls
async def fetch_dashboard_data(user_id):
    user = await get_user(user_id)
    orders = await get_orders(user_id)
    notifications = await get_notifications(user_id)
    return {"user": user, "orders": orders, "notifications": notifications}


# Bad: S3 in a loop
def process_files(bucket, keys):
    s3 = boto3.client("s3")
    for key in keys:
        s3.get_object(Bucket=bucket, Key=key)


# Bad: New connection per request
def handle_request(request):
    import psycopg2
    conn = psycopg2.connect(host="localhost", dbname="mydb")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


# Good: Fixed version with bulk query
async def get_order_details_fixed(order_ids):
    orders = await db.query().filter(id__in=order_ids).all()
    return orders


# Good: Parallel async
async def fetch_dashboard_data_fixed(user_id):
    import asyncio
    user, orders, notifications = await asyncio.gather(
        get_user(user_id),
        get_orders(user_id),
        get_notifications(user_id),
    )
    return {"user": user, "orders": orders, "notifications": notifications}
