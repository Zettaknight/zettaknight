#!/bin/bash
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

version="1.0"

function show_help () {
cat <<EOF

version $version

USAGE:
$0 [dsbmef]

DESCRIPTION:
        default protocol will use an /etc/xinetd.d/<file> daemon on remote server, you will need to use scp (-e) if this is not setup

OPTIONS:
required
        -s subject of message
        -m message body, must be a string
        -r message recipients, will accept multiple arguments separated by whitespace
optional
        -a [message attachment] full path to object to attach to message
EOF
}

function check_previous () {
                local exit_status=$?
                if ! [ $exit_status == 0 ]; then
                        echo "${exit_status} : $@"
                        clean_up
                        exit 1
                fi
}

############# flags ###############
email_attachment_flag=0


while getopts "s:m:r:a::?" OPTION
do
         case $OPTION in
                s)
                    email_subject="$OPTARG"
                    ;;
                m)
                    email_body="$OPTARG"
                    ;;
                r)
                    email_recipient="$OPTARG"
                    ;;
                a)
                    email_attachment="$OPTARG"
                    email_attachment_flag=1
                    ;;
                :)
                    show_help
                    exit 1
                    ;;
                help)
                    show_help
                    exit 1
                    ;;
        esac
done

if [[ -z "$email_subject" ]] || [[ -z "$email_body" ]] || [[ -z "$email_recipient" ]]; then
    echo "required arguments missing"
    echo "email subject : $email_subject"
    echo "email body : $email_body"
    echo "email_recipient : $email_recipient"
    show_help
    exit 1
fi

if ! which mailx &> /dev/null; then
    echo "mailx does not exist in PATH, will not send email"
    exit 1
fi

if [ -f "$email_body" ]; then
    echo "noticed message body is a file, using cat to display the contents of the message"
    email_body=$(cat $email_body) #this will get executed in the following block
fi

#if [ $email_attachment_flag == 1 ]; then
#    echo "$email_body" | mailx -s "$email_subject" -a $email_attachment "$email_recipient"
#    check_previous "echo $email_body | mailx -s $email_subject -a $email_attachment $email_recipient"
#else

echo "sending mail to $email_recipient"
cat <<EOF | mailx -s "$email_subject" "$email_recipient"
$email_body
EOF
check_previous "failed to send email to $email_recipient"

#fi
