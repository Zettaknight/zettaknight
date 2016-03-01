function printcolors () {

        if [ $# == 2 ]; then
                color=$1
                msg=$2
        else
                echo "function printcolors expects 2 arguments (color, msg)"
                exit 1
        fi

        end_color_code='\033[0m'

        if [ $color == "green" ]; then
                color_code='\033[92m'
        elif [ $color == "blue" ]; then
                color_code='\033[96m'
        elif [ $color == "yellow" ]; then
                color_code='\033[93m'
        elif [ $color == "red" ]; then
                color_code='\033[91m'
        elif [ $color == "pink" ]; then
                color_code='\033[95m'
        else
                echo "$color not recognized"
                exit 1
        fi

    if [ $color_flag = 1 ]; then
        echo -e "${color_code}${msg}${end_color_code}"
    else
        echo -e "$msg"
    fi
}
