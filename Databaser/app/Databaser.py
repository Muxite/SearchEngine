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
    def __init__(self, sync_period=30, timeout=120):
        """
        Stores link-tags pairs into a MySQL database. Uses 3 tables, "links", "tags", "junction".
        :param redis_client: Redis to connect to.
        :param connection: MySQL connection.
        :param sync_period: How often data transfer is done.
        :param timeout: Time until automatic shutdown.
        """

        self.redis_client = None
        self.mysql_connection = None
        self.mysql_cursor = None
        self.sync_period = sync_period
        self.timeout = timeout
        self.active = False
        self.await_stream()


    def setup(self):
        self.mysql_cursor.execute("CREATE TABLE IF NOT EXISTS links ("
                            "id INT AUTO_INCREMENT PRIMARY KEY, "
                            "link VARCHAR(2048) NOT NULL")
        self.mysql_cursor.execute("CREATE TABLE IF NOT EXISTS tags ("
                            "id INT AUTO_INCREMENT PRIMARY KEY, "
                            "link VARCHAR(64) NOT NULL")
        self.mysql_cursor.execute("CREATE TABLE IF NOT EXISTS junction ("
                            "link_id INT, "
                            "tag_id INT, "
                            "PRIMARY KEY (link_id, tag_id),"
                            "FOREIGN KEY (link_id) REFERENCES links(id) ON DELETE CASCADE,"
                            "FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE)")
        self.mysql_connection.commit()

    def connect(self, redis_host, redis_port, mysql_host, mysql_port,
                      mysql_user, mysql_password, mysql_database ):
        redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)
        mysql_connection = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        self.mysql_connection = mysql_connection
        self.mysql_cursor = mysql_connection.cursor()
        self.redis_client = redis_client


    def quit(self):
        self.active = False

    def await_stream(self, interval=5, retries=20):
        """
        Start the stream and stream timer when a connection is established.
        """

        while not self.active:
            if not self.mysql_connection or not self.mysql_cursor or not self.redis_client:
                if retries < 0:
                    return
                retries -= 1
                time.sleep(interval)
            else:
                self.setup()
                self.stream(self.timeout)

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
            link, tags = json.loads(self.redis_client.lpop("link_tag_queue"))
            print(f"Databasing: link: {link}    tags: {tags}")
            self.mysql_cursor.execute("INSERT IGNORE INTO links (link) VALUES (%s)", (link,))
            tag_tuple = *tags,
            self.mysql_cursor.executemany("INSERT IGNORE INTO tags VALUES %s", tag_tuple)

            # get all ids for link and all tags
            self.mysql_cursor.execute("SELECT id FROM links WHERE link_id = %s", (link,))
            link_id = self.mysql_cursor.fetchone()[0]
            self.mysql_cursor.execute("INSERT IGNORE INTO junction VALUES %s", (link_id,))
            junction_row = []
            for tag in tags:
                self.mysql_cursor.execute("SELECT id FROM tags WHERE link = %s", (tag,))
                tag_id = self.mysql_cursor.fetchone()[0]
                junction_row.append((link_id, tag_id))

            # fill in junction table.
            self.mysql_cursor.executemany("INSERT IGNORE INTO junction VALUES (%s, %s)", junction_row)
            self.mysql_connection.commit()

            return True
        except TypeError:
            return False


def run():
    args = parse_args()

    databaser = Databaser(
        sync_period=args.sync_period,
        timeout=args.timeout
    )

    databaser.connect(
        args.redis_host,
        args.redis_port,
        args.mysql_host,
        args.mysql_port,
        args.mysql_user,
        args.mysql_password,
        args.mysql_database
    )


if __name__ == "__main__":
    run()
