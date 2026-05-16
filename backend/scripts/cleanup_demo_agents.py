"""Cleanup script to remove demo agents from the database."""

import psycopg2

DEMO_SYSTEM_IDS = [
    "athena",
    "argus",
    "clerkbot",
    "Athena",
    "Argus",
    "ClerkBot",
]

DSN = "postgresql://playbook:playbook123@172.27.144.112:5432/playbook"


def main():
    conn = psycopg2.connect(DSN)
    cur = conn.cursor()

    # Delete known demo agents
    cur.execute(
        "DELETE FROM agents WHERE system_id = ANY(%s) RETURNING system_id;",
        (DEMO_SYSTEM_IDS,),
    )
    deleted_known = cur.fetchall()

    # Delete agents with system_id starting with demo-
    cur.execute(
        "DELETE FROM agents WHERE system_id LIKE 'demo-%' RETURNING system_id;",
    )
    deleted_demo_prefix = cur.fetchall()

    conn.commit()
    cur.close()
    conn.close()

    print(f"Deleted {len(deleted_known)} known demo agents: {[r[0] for r in deleted_known]}")
    print(f"Deleted {len(deleted_demo_prefix)} demo-prefixed agents: {[r[0] for r in deleted_demo_prefix]}")


if __name__ == "__main__":
    main()
