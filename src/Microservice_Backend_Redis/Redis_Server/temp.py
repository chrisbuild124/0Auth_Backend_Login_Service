import redis
from typing import Optional
import datetime
import time

TIME_UNTIL_EXPIRED = 15 # Seconds until token is considered expired

def get_client():
    return redis.Redis(
        host='localhost',
        port=6379,
        password='o3rne23ojrno2jnfiunf2o',    # remove if not using auth
        db=0,
        decode_responses=True             # nice: returns str instead of bytes
    )

def create_user(r: redis.Redis, user_id: int, JWT: str) -> None:
    key = f"user:{user_id}"
    # Use a hash to store structured fields
    r.hset(key, mapping={"JWT": JWT, "last_updated": datetime.datetime.now().isoformat()})

def read_user(r: redis.Redis, user_id: int) -> Optional[dict]:
    key = f"user:{user_id}"
    data = r.hgetall(key)
    return data if data else None

def update_user_token(r: redis.Redis, user_id: int, JWT: str) -> bool:
    key = f"user:{user_id}"
    if r.exists(key):
        r.hset(key, mapping={"JWT": JWT, "last_updated": datetime.datetime.now().isoformat()})
        return True
    return False

def delete_user(r: redis.Redis, user_id: int) -> int:
    key = f"user:{user_id}"
    return r.delete(key)  # returns 1 if deleted, 0 if not found

def is_token_expired(r: redis.Redis, user_id: int) -> bool:
    key = f"user:{user_id}"
    data = r.hgetall(key)
    if not data:
        return True  # User doesn't exist, so token is expired

    last_updated_str = data.get("last_updated")
    if not last_updated_str:
        return True  # No last_updated field, so token is expired

    try:
        now = datetime.datetime.now()
        last_updated = datetime.datetime.fromisoformat(last_updated_str)
        time_diff = (now - last_updated).total_seconds()
        return time_diff > TIME_UNTIL_EXPIRED
    except ValueError:
        return True  # Invalid date format, so token is expired

if __name__ == "__main__":
    r = get_client()

    # CREATE
    create_user(r, 1001, "1234")

    # READ
    user = read_user(r, 1001)
    print("User:", user)

    # UPDATE
    updated = update_user_token(r, 1001, "5678")
    print("Updated:", updated)

    print(is_token_expired(r, 1001))
    time.sleep(TIME_UNTIL_EXPIRED + 1) # Wait to ensure token is expired
    print(is_token_expired(r, 1001))

    # DELETE
    deleted = delete_user(r, 1001)
    print("Deleted:", deleted)

    # Verify deletion
    print("After deletion:", read_user(r, 1001))