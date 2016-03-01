function ssh_over () {
    ssh_cmd="$@"
    
    if [ -z "$ssh" ]; then
        ssh=$(which ssh)
        if [ -x "$ssh" ]; then
            ssh="/bin/ssh"
        fi
    fi
    
    if [ -z "$remote_ssh" ]; then
        echo "variable remote_ssh is required for function ssh_over, not set"
        exit 1
    fi
    
    if ! [[ -z "$identity_file" ]]; then
        if [[ -f "$identity_file" ]]; then
            $ssh -q -i "$identity_file" "$remote_ssh" "$ssh_cmd"
        else
            echo "$identity_file is not accessible, cannot use"
            $ssh -q $remote_ssh "$ssh_cmd"
        fi
    else
        $ssh -q $remote_ssh "$ssh_cmd"
    fi

}
