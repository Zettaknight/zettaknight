#!/bin/bash

error_max=3 #max time allowed, in seconds, for ping to error before reporting the error
wait_time=1 #time ping waits for a response, in seconds
sleep_time=5 #time to sleep between successful tests, keeps from pinging every second for
test_address="google.com" #test address to ping

date_time=$(date '+%Y%m%d_%H%M')
logfile="/home/matt/Dropbox/${date_time}_outages.txt"
error_count=0

while true; do
        if ! ping -q -c 1 -W $wait_time "$test_address" &> /dev/null; then
            error_count=$(( $error_count + 1 ))
            echo "ping failure #${error_count}"
            if [ $error_count == 1 ]; then
                error_date=$(date)
                error_date_sec=$(date +%s)
            fi
        else
            if [[ $error_count != 0 ]]; then
                echo "ping succeeded, resetting error count"
            fi
            error_count=0 #reset counter if ping gets through
            sleep $sleep_time 
        fi
        
        if [[ $error_count -ge $error_max ]]; then
            echo "lost $error_date" | tee -a $logfile
            recover_int=0
            while [[ $recover_int == 0 ]]; do
                if ping -q -c 1 -W $wait_time "$test_address" &> /dev/null; then
                    recover_date=$(date)
                    recover_date_sec=$(date +%s)
                    recover_time_sec=$(( $recover_date_sec - $error_date_sec ))
                    recover_int=1
                    error_count=0
                    
                    echo -e "recovered $recover_date after $recover_time_sec seconds\n" | tee -a $logfile 
                fi
            done
        fi
done
