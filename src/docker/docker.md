It appears there's a mismatch between the architecture of your server and the Docker Compose binary you've downloaded. The error message `Exec format error` suggests that the binary file's format isn't compatible with your system's architecture.

If you're not sure about your system's architecture, you can check it by running this command:

```bash
uname -m
```

If the output is `x86_64`, you're running an x86_64 system (also known as amd64). If it's `armv7l`, you're running an ARMv7 system, and so on.

Depending on the output, you'll need to download the appropriate Docker Compose binary. For example, if your system is `x86_64`, you should download the x86_64 binary:

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.1.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
```

Then set the permissions and try again:

```bash
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

Please replace `v2.1.1` with the latest version of Docker Compose if it's not `v2.1.1`.



The following steps can be used to backup Docker volumes:

1. **MySQL Database**: For MySQL, you can use `mysqldump` command to create a backup of your database. Assuming you have `mysqldump` installed on your host, you can run the following command:

    ```bash
    docker exec CONTAINER /usr/bin/mysqldump -u root --password=root DATABASE > backup.sql
    ```
    Replace `CONTAINER` with the name of your MySQL container, `root` after `--password=` with your MySQL root password, and `DATABASE` with the name of your database. `backup.sql` will be the file in which the backup is saved.

2. **Redis**: To back up a Redis database, you need to copy the `dump.rdb` file that Redis automatically creates. To copy this file to your host, you can use the following command:

    ```bash
    docker cp CONTAINER:/data/dump.rdb .
    ```
    Replace `CONTAINER` with the name of your Redis container. This will copy the `dump.rdb` file to the current directory on your host.

3. **MongoDB**: MongoDB's `mongodump` tool can be used to create backups. The following command can be used to create a backup:

    ```bash
    docker exec CONTAINER /bin/bash -c 'mongodump --archive' > db.dump
    ```
    Replace `CONTAINER` with the name of your MongoDB container. This will save the backup in a file named `db.dump` on your host.

To restore the backups:

1. **MySQL**:

    ```bash
    cat backup.sql | docker exec -i CONTAINER /usr/bin/mysql -u root --password=root DATABASE
    ```
2. **Redis**: First, you need to start a temporary Redis container with the volume attached:

    ```bash
    docker run --rm -v redis_data:/data -v /backup:/backup redis:latest bash -c 'cp /data/dump.rdb /backup'
    ```
    Then you can copy the `dump.rdb` file to the `redis_data` volume:

    ```bash
    docker cp dump.rdb CONTAINER:/data
    ```
3. **MongoDB**:

    ```bash
    docker exec -i CONTAINER /bin/bash -c 'mongorestore --archive' < db.dump
    ```
In all of the above, `CONTAINER` should be replaced with your container's name, and you may need to adjust database names, usernames, passwords, and file paths based on your actual configuration.

**Note**: Docker volumes can also be backed up by copying the data from the volumes to the host using the `docker cp` command, and vice versa. However, using the proper backup tools for each database is generally a better approach as it ensures data consistency and integrity.

Finally, please make sure to store your backup files safely, ideally on a separate backup server or storage service, and encrypt them if they contain sensitive data.