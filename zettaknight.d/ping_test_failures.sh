#!/bin/bash

error_max=3 #max time allowed, in seconds, for ping to error before reporting the error
wait_time=1 #time ping waits for a response, in seconds
sleep_time=5 #time to sleep between successful tests, keeps from pinging every second for
discard_time=10 #number of seconds the internet must be out before recording it as unavailable
start_address_array=('google.com' 'clemson.edu' 'microsoft.com' 'att.com' 'yahoo.com') #test address to ping

date_time=$(date '+%Y%m%d_%H%M')
logfile="/home/matt/Dropbox/${date_time}_outages.txt"
error_count=0

#test ping nodes
end_address_array=()

echo "testing address bank"
for test_address in "${start_address_array[@]}"; do
    if ping -q -c 2 -W $wait_time "$test_address" &> /dev/null; then
        echo -e "\tVALID: $test_address"
        end_address_array+=("$test_address")
    else
        echo -e "\tREMOVED: $test_address"    
    fi
done

while true; do
    for test_address in "${end_address_array[@]}"; do
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
            echo "lost $error_date"
            recover_int=0
            while [[ $recover_int == 0 ]]; do
                if ping -q -c 1 -W $wait_time "$test_address" &> /dev/null; then
                    recover_date=$(date)
                    recover_date_sec=$(date +%s)
                    recover_time_sec=$(( $recover_date_sec - $error_date_sec ))
                    recover_int=1
                    error_count=0
                    
                    if [[ "$recover_time_sec" -ge "$discard_time" ]]; then
                        echo "lost $error_date" | tee -a $logfile
                        echo -e "recovered $recover_date after $recover_time_sec seconds\n" | tee -a $logfile
                    else
                        echo -e "recovered $recover_date after $recover_time_sec seconds\nthis is within the set discard time of $discard_time, this event will not be recorded"
                    fi
                fi
            done
        fi
    done
done
