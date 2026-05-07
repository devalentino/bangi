import time

import pymysql
import pymysql.cursors


def main():
    connection = pymysql.connect(
        host='46.101.230.34',
        user='bangi',
        password='ebb15b5ee517881c557075a987fccac5',
        database='bangi_tracker',
        port=8306,  # Default MySQL port
        cursorclass=pymysql.cursors.DictCursor  # Returns results as dictionaries
    )

    filesystem = '/dev/sda'
    mountpoint = '/'
    total_bytes = 24299968
    used_bytes = 9710432
    available_bytes = 14573152
    used_percent = 40
    created_at = int(time.time())

    try:
        with connection.cursor() as cursor:
            for i in range(8000):
                sql = "INSERT INTO health_disk_utilization SET created_at = %s, filesystem = %s, mountpoint = %s, total_bytes = %s, used_bytes = %s, available_bytes = %s, used_percent = %s"
                cursor.execute(sql, (created_at, filesystem, mountpoint, total_bytes, used_bytes, available_bytes, used_percent))

                created_at -= 3600
                used_bytes -= 100
                available_bytes += 100
                used_percent = int(used_bytes / total_bytes * 100)

                print(i)

        connection.commit()

    finally:
        connection.close()


if __name__ == '__main__':
    main()
