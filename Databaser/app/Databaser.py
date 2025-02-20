import redis
import json
import argparse
import mysql.connector
from utils import delayed_action
import time

def parse_args():
    parser = argparse.ArgumentParser(description='Store links and tags in a database')
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds.")
    parser.add_argument("--sync_period", type=int, default=30, help="Sync period in seconds.")
    parser.add_argument("--redis_host", type=str, help="Redis host.")
    parser.add_argument("--redis_port", type=int, default=6379, help="Redis port.")
    parser.add_argument("--mysql_host", type=str, default="host", help="MySQL host.")
    parser.add_argument("--mysql_port", type=int, default=3306, help="MySQL port.")
    parser.add_argument("--mysql_user", type=str, default="user")
    parser.add_argument("--mysql_password", type=str, default="pw")
    parser.add_argument("--mysql_database", type=str, default="db")
    return parser.parse_args()


class Databaser:
    def __init__(self, redis_client, connection, sync_period=30, timeout=120):
        """
        Stores link-tags pairs into a MySQL database. Uses 3 tables, "links", "tags", "junction".
        :param redis_client: Redis to connect to.
        :param connection: MySQL connection.
        :param sync_period: How often data transfer is done.
        :param timeout: Time until automatic shutdown.
        """
        self.redis = redis_client
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.sync_period = sync_period
        self.timeout = timeout
        self.active = False
        self.setup()
        self.stream(self.timeout)


    def setup(self):
        self.cursor.execute("CREATE TABLE IF NOT EXISTS links ("
                            "id INT AUTO_INCREMENT PRIMARY KEY, "
                            "link VARCHAR(2048) NOT NULL")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS tags ("
                            "id INT AUTO_INCREMENT PRIMARY KEY, "
                            "link VARCHAR(64) NOT NULL")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS junction ("
                            "link_id INT, "
                            "tag_id INT, "
                            "PRIMARY KEY (link_id, tag_id),"
                            "FOREIGN KEY (link_id) REFERENCES links(id) ON DELETE CASCADE,"
                            "FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE)")
        self.connection.commit()

    def quit(self):
        self.active = False

    def stream(self, timeout):
        """
        Continuously move data from Redis to MySQL database.
        :param timeout: Pause time after failed movement.
        """
        self.active = True
        delayed_action(timeout, self.quit)
        while self.active:
            if not self.transfer():
                time.sleep(self.sync_period)

    def transfer(self):
        """
        Transfers 1 link-tags pair into the database.
        :return: True if successful, False otherwise.
        """
        try:
            link, tags = json.loads(self.redis.lpop("link_tag_queue"))
            self.cursor.execute("INSERT IGNORE INTO links (link) VALUES (%s)", (link,))
            tag_tuple = *tags,
            self.cursor.executemany("INSERT IGNORE INTO tags VALUES %s", tag_tuple)

            # get all ids for link and all tags
            self.cursor.execute("SELECT id FROM links WHERE link_id = %s", (link,))
            link_id = self.cursor.fetchone()[0]
            self.cursor.execute("INSERT IGNORE INTO junction VALUES %s", (link_id,))
            junction_row = []
            for tag in tags:
                self.cursor.execute("SELECT id FROM tags WHERE link = %s", (tag,))
                tag_id = self.cursor.fetchone()[0]
                junction_row.append((link_id, tag_id))

            # fill in junction table.
            self.cursor.executemany("INSERT IGNORE INTO junction VALUES (%s, %s)", junction_row)
            self.connection.commit()

            return True
        except TypeError:
            return False


def run():
    args = parse_args()
    r = redis.Redis(
        host=args.redis_host,
        port=args.redis_port,
        db=0
    )

    c = mysql.connector.connect(
        host=args.mysql_host,
        port=args.mysql_port,
        user=args.mysql_user,
        password=args.mysql_password,
        database=args.mysql_database
    )

    databaser = Databaser(
        redis_client=r,
        connection=c,
        sync_period=args.sync_period,
        timeout=args.timeout
    )


if __name__ == "__main__":
    run()
