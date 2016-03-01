function show_help () {
cat << EOF
version $version

    DESCRIPTION:
        $(basename $0)

    $setopts_help
EOF
}


function setopts () {
    local opt_type=$1 
    local pattern=$2
    
    if [[ -z $setopts_help ]]; then
        setopts_help=$(cat << EOF
        Options:
            ${pattern}: 
                - $4
EOF
)
    else
        setopts_help="$setopts_help $(cat << EOF
            
            ${pattern}:
                - $4
EOF
)"
    fi
        
    local pattern=$(echo $pattern | sed 's/|/ /g')
    var=$3 #set global var for use outside function
    local num_args=${#BASH_ARGV[@]}
        if [[ $num_args > 0 ]]; then
            if [[ "$opt_type" == "flag" || "$opt_type" == "switch" ]]; then
                eval $var="0"
            fi
            local last_index_num=$(( $num_args - 1 )) #5th argument would be the 4th index
            for global_bash_index in $(seq 0 ${last_index_num}); do #for index in array positions 0-end
                for blah in $pattern; do
                    case ${BASH_ARGV[$global_bash_index]} in
                        $blah)
                            if [[ "$opt_type" == "var" ]]; then
                                arg="${BASH_ARGV[$global_bash_index]}"
                                val="${BASH_ARGV[$(( $global_bash_index - 1 ))]}"
                                
                                if [ "$arg" == "$val" ]; then
                                    echo "setopts error, $arg must have a value"
                                    exit 1
                                fi
                                
                                eval $var='$val'
                                
                            elif [[ "$opt_type" == "flag" || "$opt_type" == "switch" ]]; then
                                eval $var=1
                            else
                                echo -e "invalid option type passed: $opt_type\nValid types are var, switch, and flag."
                            fi
                            break
                            ;;
                        *)
                            continue
                            ;;
                    esac
                done
            done  
        fi
}
