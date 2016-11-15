#
#    Copyright (c) 2015-2016 Matthew Carter, Ralph M Goodberlet.
#
#    This file is part of Zettaknight.
#
#    Zettaknight is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Zettaknight is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Zettaknight.  If not, see <http://www.gnu.org/licenses/>.
#

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
                                
                            elif [[ $"opt_type" == "int" ]]; then
                            
                                arg="${BASH_ARGV[$global_bash_index]}"
                                val="${BASH_ARGV[$(( $global_bash_index - 1 ))]}"
                                
                                if [ "$arg" == "$val" ]; then
                                    echo "setopts error, $arg must have a value"
                                    exit 1
                                fi
                                
                                if ! [[ $val =~ ^[-+]?[0-9]+$ ]]; then #test if integer
                                    echo "$val for $arg is not an integer"
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
