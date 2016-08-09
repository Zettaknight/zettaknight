#!/bin/bash

#file locations to write
yum_repo="/etc/yum.repos.d/ol6_spacewalk22_client.repo"
spacewalk_key="/usr/share/rhn/RHN-ORG-TRUSTED-SSL-CERT"
rhn_file="/etc/sysconfig/rhn/osad.conf"

function check_previous () {
    local exit_status=$?
    local msg="$@"

    if ! [ $exit_status == 0 ]; then
        echo "${exit_status} : $@"
        exit 1
    fi
}

function install_pkg () {
    local pkge="$@"
    
    if [ -z "$pkg" ]; then
        echo -e "\ninstalling $pkg"
        yum install "$pkg" -y --nogpgcheck
        check_previous "failed to install $pkg"
    fi    
}

function add_ol6_repo () {
    echo -e "\ncreating $yum_repo"
cat > $yum_repo <<EOF
[ol6_spacewalk22_client_x86_64] 
name=Spacewalk Client 2.2 for Oracle Linux ($basearch) 
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-oracle 
enabled=1 
baseurl=http://ccitsw01.clemson.edu/pub/repo/ol6_spacewalk22_client_x86_64 
humanname=Spacewalk Client 2.2 for Oracle Linux ($basearch) 
gpgcheck=0
EOF

check_previous "failed to write $yum_repo"
}

function add_spacewalk_key () {
    echo -e "\nadding $spacewalk_key"
cat > $spacewalk_key <<EOF
-----BEGIN CERTIFICATE----- 
MIIENjCCAx6gAwIBAgIBATANBgkqhkiG9w0BAQUFADBvMQswCQYDVQQGEwJTRTEU 
MBIGA1UEChMLQWRkVHJ1c3QgQUIxJjAkBgNVBAsTHUFkZFRydXN0IEV4dGVybmFs 
IFRUUCBOZXR3b3JrMSIwIAYDVQQDExlBZGRUcnVzdCBFeHRlcm5hbCBDQSBSb290 
MB4XDTAwMDUzMDEwNDgzOFoXDTIwMDUzMDEwNDgzOFowbzELMAkGA1UEBhMCU0Ux 
FDASBgNVBAoTC0FkZFRydXN0IEFCMSYwJAYDVQQLEx1BZGRUcnVzdCBFeHRlcm5h 
bCBUVFAgTmV0d29yazEiMCAGA1UEAxMZQWRkVHJ1c3QgRXh0ZXJuYWwgQ0EgUm9v 
dDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALf3GjPm8gAELTngTlvt 
H7xsD821+iO2zt6bETOXpClMfZOfvUq8k+0DGuOPz+VtUFrWlymUWoCwSXrbLpX9 
uMq/NzgtHj6RQa1wVsfwTz/oMp50ysiQVOnGXw94nZpAPA6sYapeFI+eh6FqUNzX 
mk6vBbOmcZSccbNQYArHE504B4YCqOmoaSYYkKtMsE8jqzpPhNjfzp/haW+710LX 
a0Tkx63ubUFfclpxCDezeWWkWaCUN/cALw3CknLa0Dhy2xSoRcRdKn23tNbE7qzN 
E0S3ySvdQwAl+mG5aWpYIxG3pzOPVnVZ9c0p10a3CitlttNCbxWyuHv77+ldU9U0 
WicCAwEAAaOB3DCB2TAdBgNVHQ4EFgQUrb2YejS0Jvf6xCZU7wO94CTLVBowCwYD 
VR0PBAQDAgEGMA8GA1UdEwEB/wQFMAMBAf8wgZkGA1UdIwSBkTCBjoAUrb2YejS0 
Jvf6xCZU7wO94CTLVBqhc6RxMG8xCzAJBgNVBAYTAlNFMRQwEgYDVQQKEwtBZGRU 
cnVzdCBBQjEmMCQGA1UECxMdQWRkVHJ1c3QgRXh0ZXJuYWwgVFRQIE5ldHdvcmsx 
IjAgBgNVBAMTGUFkZFRydXN0IEV4dGVybmFsIENBIFJvb3SCAQEwDQYJKoZIhvcN 
AQEFBQADggEBALCb4IUlwtYj4g+WBpKdQZic2YR5gdkeWxQHIzZlj7DYd7usQWxH 
YINRsPkyPef89iYTx4AWpb9a/IfPeHmJIZriTAcKhjW88t5RxNKWt9x+Tu5w/Rw5 
6wwCURQtjr0W4MHfRnXnJK3s9EK0hZNwEGe6nQY1ShjTK3rMUUKhemPR5ruhxSvC 
Nr4TDea9Y355e6cJDUCrat2PisP29owaQgVR1EX1n6diIWgVIEM8med8vSTYqZEX 
c4g/VhsxOBi0cQ+azcgOno4uG+GMmIPLHzHxREzGBHNJdmAPx/i9F4BrLunMTA5a 
mnkPIAou1Z5jJh5VkpTYghdae9C8x49OhgQ= 
-----END CERTIFICATE----- 
-----BEGIN CERTIFICATE----- 
MIIFdzCCBF+gAwIBAgIQE+oocFv07O0MNmMJgGFDNjANBgkqhkiG9w0BAQwFADBv 
MQswCQYDVQQGEwJTRTEUMBIGA1UEChMLQWRkVHJ1c3QgQUIxJjAkBgNVBAsTHUFk 
ZFRydXN0IEV4dGVybmFsIFRUUCBOZXR3b3JrMSIwIAYDVQQDExlBZGRUcnVzdCBF 
eHRlcm5hbCBDQSBSb290MB4XDTAwMDUzMDEwNDgzOFoXDTIwMDUzMDEwNDgzOFow 
gYgxCzAJBgNVBAYTAlVTMRMwEQYDVQQIEwpOZXcgSmVyc2V5MRQwEgYDVQQHEwtK 
ZXJzZXkgQ2l0eTEeMBwGA1UEChMVVGhlIFVTRVJUUlVTVCBOZXR3b3JrMS4wLAYD 
VQQDEyVVU0VSVHJ1c3QgUlNBIENlcnRpZmljYXRpb24gQXV0aG9yaXR5MIICIjAN 
BgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAgBJlFzYOw9sIs9CsVw127c0n00yt 
UINh4qogTQktZAnczomfzD2p7PbPwdzx07HWezcoEStH2jnGvDoZtF+mvX2do2NC 
tnbyqTsrkfjib9DsFiCQCT7i6HTJGLSR1GJk23+jBvGIGGqQIjy8/hPwhxR79uQf 
jtTkUcYRZ0YIUcuGFFQ/vDP+fmyc/xadGL1RjjWmp2bIcmfbIWax1Jt4A8BQOujM 
8Ny8nkz+rwWWNR9XWrf/zvk9tyy29lTdyOcSOk2uTIq3XJq0tyA9yn8iNK5+O2hm 
AUTnAU5GU5szYPeUvlM3kHND8zLDU+/bqv50TmnHa4xgk97Exwzf4TKuzJM7UXiV 
Z4vuPVb+DNBpDxsP8yUmazNt925H+nND5X4OpWaxKXwyhGNVicQNwZNUMBkTrNN9 
N6frXTpsNVzbQdcS2qlJC9/YgIoJk2KOtWbPJYjNhLixP6Q5D9kCnusSTJV882sF 
qV4Wg8y4Z+LoE53MW4LTTLPtW//e5XOsIzstAL81VXQJSdhJWBp/kjbmUZIO8yZ9 
HE0XvMnsQybQv0FfQKlERPSZ51eHnlAfV1SoPv10Yy+xUGUJ5lhCLkMaTLTwJUdZ 
+gQek9QmRkpQgbLevni3/GcV4clXhB4PY9bpYrrWX1Uu6lzGKAgEJTm4Diup8kyX 
HAc/DVL17e8vgg8CAwEAAaOB9DCB8TAfBgNVHSMEGDAWgBStvZh6NLQm9/rEJlTv 
A73gJMtUGjAdBgNVHQ4EFgQUU3m/WqorSs9UgOHYm8Cd8rIDZsswDgYDVR0PAQH/ 
BAQDAgGGMA8GA1UdEwEB/wQFMAMBAf8wEQYDVR0gBAowCDAGBgRVHSAAMEQGA1Ud 
HwQ9MDswOaA3oDWGM2h0dHA6Ly9jcmwudXNlcnRydXN0LmNvbS9BZGRUcnVzdEV4 
dGVybmFsQ0FSb290LmNybDA1BggrBgEFBQcBAQQpMCcwJQYIKwYBBQUHMAGGGWh0 
dHA6Ly9vY3NwLnVzZXJ0cnVzdC5jb20wDQYJKoZIhvcNAQEMBQADggEBAJNl9jeD 
lQ9ew4IcH9Z35zyKwKoJ8OkLJvHgwmp1ocd5yblSYMgpEg7wrQPWCcR23+WmgZWn 
RtqCV6mVksW2jwMibDN3wXsyF24HzloUQToFJBv2FAY7qCUkDrvMKnXduXBBP3zQ 
YzYhBx9G/2CkkeFnvN4ffhkUyWNnkepnB2u0j4vAbkN9w6GAbLIevFOFfdyQoaS8 
Le9Gclc1Bb+7RrtubTeZtv8jkpHGbkD4jylW6l/VXxRTrPBPYer3IsynVgviuDQf 
Jtl7GQVoP7o81DgGotPmjw7jtHFtQELFhLRAlSv0ZaBIefYdgWOWnU914Ph85I6p 
0fKtirOMxyHNwu8= 
-----END CERTIFICATE----- 
-----BEGIN CERTIFICATE----- 
MIIF+TCCA+GgAwIBAgIQRyDQ+oVGGn4XoWQCkYRjdDANBgkqhkiG9w0BAQwFADCB 
iDELMAkGA1UEBhMCVVMxEzARBgNVBAgTCk5ldyBKZXJzZXkxFDASBgNVBAcTC0pl 
cnNleSBDaXR5MR4wHAYDVQQKExVUaGUgVVNFUlRSVVNUIE5ldHdvcmsxLjAsBgNV 
BAMTJVVTRVJUcnVzdCBSU0EgQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkwHhcNMTQx 
MDA2MDAwMDAwWhcNMjQxMDA1MjM1OTU5WjB2MQswCQYDVQQGEwJVUzELMAkGA1UE 
CBMCTUkxEjAQBgNVBAcTCUFubiBBcmJvcjESMBAGA1UEChMJSW50ZXJuZXQyMREw 
DwYDVQQLEwhJbkNvbW1vbjEfMB0GA1UEAxMWSW5Db21tb24gUlNBIFNlcnZlciBD 
QTCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBAJwb8bsvf2MYFVFRVA+e 
xU5NEFj6MJsXKZDmMwysE1N8VJG06thum4ltuzM+j9INpun5uukNDBqeso7JcC7v 
HgV9lestjaKpTbOc5/MZNrun8XzmCB5hJ0R6lvSoNNviQsil2zfVtefkQnI/tBPP 
iwckRR6MkYNGuQmm/BijBgLsNI0yZpUn6uGX6Ns1oytW61fo8BBZ321wDGZq0GTl 
qKOYMa0dYtX6kuOaQ80tNfvZnjNbRX3EhigsZhLI2w8ZMA0/6fDqSl5AB8f2IHpT 
eIFken5FahZv9JNYyWL7KSd9oX8hzudPR9aKVuDjZvjs3YncJowZaDuNi+L7RyML 
fzcCAwEAAaOCAW4wggFqMB8GA1UdIwQYMBaAFFN5v1qqK0rPVIDh2JvAnfKyA2bL 
MB0GA1UdDgQWBBQeBaN3j2yW4luHS6a0hqxxAAznODAOBgNVHQ8BAf8EBAMCAYYw 
EgYDVR0TAQH/BAgwBgEB/wIBADAdBgNVHSUEFjAUBggrBgEFBQcDAQYIKwYBBQUH 
AwIwGwYDVR0gBBQwEjAGBgRVHSAAMAgGBmeBDAECAjBQBgNVHR8ESTBHMEWgQ6BB 
hj9odHRwOi8vY3JsLnVzZXJ0cnVzdC5jb20vVVNFUlRydXN0UlNBQ2VydGlmaWNh 
dGlvbkF1dGhvcml0eS5jcmwwdgYIKwYBBQUHAQEEajBoMD8GCCsGAQUFBzAChjNo 
dHRwOi8vY3J0LnVzZXJ0cnVzdC5jb20vVVNFUlRydXN0UlNBQWRkVHJ1c3RDQS5j 
cnQwJQYIKwYBBQUHMAGGGWh0dHA6Ly9vY3NwLnVzZXJ0cnVzdC5jb20wDQYJKoZI 
hvcNAQEMBQADggIBAC0RBjjW29dYaK+qOGcXjeIT16MUJNkGE+vrkS/fT2ctyNMU 
11ZlUp5uH5gIjppIG8GLWZqjV5vbhvhZQPwZsHURKsISNrqOcooGTie3jVgU0W+0 
+Wj8mN2knCVANt69F2YrA394gbGAdJ5fOrQmL2pIhDY0jqco74fzYefbZ/VS29fR 
5jBxu4uj1P+5ZImem4Gbj1e4ZEzVBhmO55GFfBjRidj26h1oFBHZ7heDH1Bjzw72 
hipu47Gkyfr2NEx3KoCGMLCj3Btx7ASn5Ji8FoU+hCazwOU1VX55mKPU1I2250Lo 
RCASN18JyfsD5PVldJbtyrmz9gn/TKbRXTr80U2q5JhyvjhLf4lOJo/UzL5WCXED 
Smyj4jWG3R7Z8TED9xNNCxGBMXnMete+3PvzdhssvbORDwBZByogQ9xL2LUZFI/i 
eoQp0UM/L8zfP527vWjEzuDN5xwxMnhi+vCToh7J159o5ah29mP+aJnvujbXEnGa 
nrNxHzu+AGOePV8hwrGGG7hOIcPDQwkuYwzN/xT29iLp/cqf9ZhEtkGcQcIImH3b 
oJ8ifsCnSbu0GB9L06Yqh7lcyvKDTEADslIaeSEINxhO2Y1fmcYFX/Fqrrp1WnhH 
OjplXuXE0OPa0utaKC25Aplgom88L2Z8mEWcyfoB7zKOfD759AN7JKZWCYwk 
-----END CERTIFICATE-----
EOF

check_previous "failed to add $spacewalk_key"
}

function add_multipath_conf () {

if ! [ -f "/etc/multipath.conf" ]; then
    cat > $rhn_file <<EOF
# This is a reference file for what should be
# /etc/multipath.conf
#
defaults {
        polling_interval 10
        path_selector "service-time 0"
        path_grouping_policy multibus
        failback immediate
        max_fds 8192
        user_friendly_names yes
        find_multipaths yes
        no_path_retry fail
}

blacklist {
        devnode "^(ram|raw|loop|fd|md|dm-|sr|scd|st)[0-9]*"
        devnode "^hd[a-z]"
        devnode "^dcssblk[0-9]*"
        device {
                vendor "DGC"
                product "LUNZ"
        }
        device {
                vendor "IBM"
                product "S/390.*"
        }
        # don't count normal SATA devices as multipaths
        device {
                vendor  "ATA"
        }
        # don't count 3ware devices as multipaths
        device {
                vendor  "3ware"
        }
        device {
                vendor  "AMCC"
        }
        # nor highpoint devices
        device {
                vendor  "HPT"
        }
        device {
                vendor iDRAC
                product Virtual_CD
        }
        device {
                vendor PLDS
                product DVD+-RW_DS-8A9SH
        }
}
EOF
fi
}

function create_rhn_file () {
    echo -e "\ncreating $rhn_file"
cat > $rhn_file <<EOF
[osad] 
 
# don't change this 
systemid = /etc/sysconfig/rhn/systemid 
 
# increase for debugging output 
debug_level = 0 
 
# don't change this... used in substitutions below. 
# if you get rid of the '%(server_handler)s' bits below, 
# the *MUST* be replaced with this value... 
server_handler = /XMLRPC 
 
# Protocol to talk upstream 
proto = https 
 
# to use a server other than what up2date is configured to use, 
# do something along the lines of: 
# server_url = https://some.example.com%(server_handler)s 
# server_url = http://another.example.net:8080%(server_handler)s 
# server_url = https://yet.another.example.org:8081/XMLRPC 
server_url = %(proto)s://%(server_name)s%(server_handler)s 
 
# the following fields are inherited from up2date's configuration, 
# but are overridable in this file 
 
# enableProxy = 1 
# enableProxyAuth = 1 
# httpProxy = some.proxy.example.com:3030 
# proxyUser = proxy_user_name 
# proxyPassword = proxy_password 
 
# Use a different certificate from what up2date is using 
# This should point to the satellite certificate for 
# server_name 
osa_ssl_cert = /usr/share/rhn/RHN-ORG-TRUSTED-SSL-CERT 
 
logfile = /var/log/osad 
 
max_time_drift = 120 
 
run_rhn_check = 1 
 
# Default command to run when asked by the dispatcher 
rhn_check_command = /usr/sbin/rhn_check 
 
# By default we only use the first jabber server. 
# Turn the enable_failover option to 1 if you want the connections 
# to try Satellite's jabberd if Red Hat Proxy's is not available. 
enable_failover = 0 
 
# Enable kernel keepalive timer on the osad client side socket 
# in case the satellite/proxy side socket is closed without osad realising it 
# After 'tcp_keepalive_timeout' seconds the kernel will probe the connection 
# After 'tcp_keepalive_count' unsuccessful probes, the kernel will close the connection 
tcp_keepalive_timeout = 1800 
tcp_keepalive_count = 3  
EOF

check_previous "failed to write $rhn_file"
}

function create_sysctl () {

# Kernel sysctl configuration file for Red Hat Linux
#
# For binary values, 0 is disabled, 1 is enabled.  See sysctl(8) and
# sysctl.conf(5) for more details.

# Controls IP packet forwarding
net.ipv4.ip_forward = 0

# Controls source route verification
net.ipv4.conf.default.rp_filter = 1

# Do not accept source routing
net.ipv4.conf.default.accept_source_route = 0

# Controls the System Request debugging functionality of the kernel
kernel.sysrq = 0

# Controls whether core dumps will append the PID to the core filename.
# Useful for debugging multi-threaded applications.
kernel.core_uses_pid = 1

# Controls the use of TCP syncookies
net.ipv4.tcp_syncookies = 1

# Controls the default maxmimum size of a mesage queue
kernel.msgmnb = 65536

# Controls the maximum size of a message, in bytes
kernel.msgmax = 65536

# Controls the maximum shared segment size, in bytes
kernel.shmmax = 68719476736

# Controls the maximum number of shared memory segments, in pages
kernel.shmall = 4294967296
# set virtual memory
vm.overcommit_memory=2
vm.overcommit_ratio=100

# turn off bridge checking for iptables
net.bridge.bridge-nf-call-ip6tables = 0
net.bridge.bridge-nf-call-iptables = 0
net.bridge.bridge-nf-call-arptables = 0

# increase arp table size
net.ipv4.neigh.default.gc_thresh1 = 4096
net.ipv4.neigh.default.gc_thresh2 = 8192
net.ipv4.neigh.default.gc_thresh3 = 8192
net.ipv4.neigh.default.base_reachable_time = 86400
net.ipv4.neigh.default.gc_stale_time = 86400

# IP stack tuning
net.ipv4.tcp_timestamps=0
net.ipv4.tcp_sack=1
net.core.rmem_max = 268435456
net.core.wmem_max = 268435456
net.core.rmem_default=16777216
net.core.wmem_default=16777216
net.core.optmem_max=268435456
net.ipv4.tcp_mem=268435456 268435456 268435456
net.ipv4.tcp_rmem = 4096        1048576 268435456
net.ipv4.tcp_wmem = 4096        1048576 268435456
net.ipv4.tcp_low_latency=1
# increase the length of the processor input queue
net.core.netdev_max_backlog = 250000
# recommended default congestion control is htcp
net.ipv4.tcp_congestion_control=htcp
# recommended for hosts with jumbo frames enabled
net.ipv4.tcp_mtu_probing=1
net.ipv4.tcp_adv_win_scale=1

    
}


#####################################################
############## script start #########################
#####################################################

add_ol6_repo
install_pkg rhn-setup rhn-check rhn-client-tools rhnsd m2crypto yum-rhn-plugin osad

add_spacewalk_key
create_rhn_file

echo -e "\nregistering with spacewalk"
rhnreg_ks --force --activationkey=2-oraclelinux6-zfs-x86_64 --sslCACert=/usr/share/rhn/RHN-ORG-TRUSTED-SSL-CERT --serverUrl=https://ccitsw01.clemson.edu/XMLRPC
check_previous "failed to register with spacewalk"

echo -e "\nadding new files"
yum update -y --nogpgcheck

install_pkg zfs

install_pkg device-mapper-multipath
echo -e "\ninstalling /etc/multipath.conf"
add_multipath_conf

svn checkout https://svn.clemson.edu/svn/zfs_administration/trunk/Release /opt/clemson/zfs_scripts/
ln -s /opt/clemson/zfs_scripts/zettaknight/zettaknight.py /sbin/zettaknight

install_pkg python-yaml


