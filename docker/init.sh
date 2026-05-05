#!bin/bash

if [ -d "/home/frappe/frappe-bench/apps/frappe" ]; then
    echo "Bench already exists, skipping init"
    cd frappe-bench
    bench start
else
    echo "Creating new bench..."
fi

export PATH="${NVM_DIR}/versions/node/v${NODE_VERSION_DEVELOP}/bin/:${PATH}"

bench init --skip-redis-config-generation frappe-bench

cd frappe-bench

# Use containers instead of localhost
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

# Remove redis, watch from Procfile
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile

bench get-app erpnext
bench get-app https://github.com/DevOpsEdupan/education --branch edupan

bench new-site education.localhost \
--force \
--mariadb-root-password ScureP@ssw0rd202020 \
--admin-password admin \
--no-mariadb-socket

bench --site education.localhost install-app erpnext
bench --site education.localhost install-app education
bench --site education.localhost set-config developer_mode 0
bench --site education.localhost enable-scheduler
bench --site education.localhost clear-cache
bench --site education.localhost set-config host_name https://education.localhost
bench --site education.localhost migrate
bench use education.localhost

bench start