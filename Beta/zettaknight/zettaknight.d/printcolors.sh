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
