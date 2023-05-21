The error message you're seeing suggests that the GPG keys installed on your system are not correct for the packages you're trying to install from the "MySQL 8.0 Community Server" repository. 

Here's a step-by-step guide to resolve this issue:

1. Remove the current MySQL repository package:

    ```bash
    sudo yum remove mysql80-community-release
    ```

2. Clear the yum cache:

    ```bash
    sudo yum clean all
    ```

3. Download the correct repository package from the MySQL website. As of my knowledge cutoff in September 2021, the MySQL Yum Repository can be obtained from here: https://dev.mysql.com/downloads/repo/yum/. You would select the version that's appropriate for your system, e.g., for CentOS 7:

    ```bash
    wget https://dev.mysql.com/get/mysql80-community-release-el7-7.noarch.rpm
    ```

    Please verify the correct link from the official MySQL website since the above link may have changed.

4. Install the downloaded repository package:

    ```bash
    sudo yum localinstall mysql80-community-release-el7-7.noarch.rpm
    ```

5. Now, try updating your system again:

    ```bash
    sudo yum update -y
    ```

The above steps should resolve the issue you're facing. If you're still encountering errors, I recommend reaching out to the MySQL community or a system administrator for further assistance.