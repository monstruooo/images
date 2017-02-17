#!/bin/bash

function dnsme_api_py () {

request_date=$(
{ echo -n "$(date -u -R) " ; date -u +%Z ; } | cut -s -d' ' -f1-5,7
)

hmac=$(echo -n "$request_date" | openssl sha1 -hmac "$dnsme_secret_key" | sed 's/.*= //g')

# http headers
api_key_H="x-dnsme-apiKey:$dnsme_api_key"
hmac_H="x-dnsme-hmac:$hmac"
req_date_H="x-dnsme-requestDate:$request_date"
content_type_H="content-type:application/json"
accept_type_H="accept:application/json"
local api_uri=$1
shift
api_uri=${api_uri#*/dns/managed/} # backward compatibility for calls that use full url instead of uri

local res
res=$(curl -s -S -H "$api_key_H" -H "$hmac_H" -H "$req_date_H" -H "$content_type_H" -H "$accept_type_H" https://api.dnsmadeeasy.com/V2.0/dns/managed/$api_uri "$@" 2>&1 ) ||
{ code=$? ; echo Curl failed | egrep --color '.*' ; return $code ; }
export res

if ! python << 'EOF'
import os, sys, json
res = os.environ['res']
if res == "":
    sys.exit(0)
res = json.loads(res)
print (json.dumps(res,indent=4))
EOF
then
    printf '\n %s \n\n' "DNSME Request failed" | egrep -C 3 --color '.*' 1>&2
    [[ "$res" =~ '<html>' ]] && echo "$res" | lynx -dump --stdin 1>&2 || echo "$res" 1>&2
    return 1
fi
} # end dnsme_api_py

function dnsme_domains_list_py () {
local res
export res
res=$(dnsme_api  http://api.dnsmadeeasy.com/V2.0/dns/managed/) || return 1
python << EOF || echo "$res"
import os,sys,json
res = json.loads(os.environ['res'])
domains=res['data']

for domain in res['data']:
    print ( '%s' % domain['name'])
# print (json.dumps(data, indent=3))
EOF
}

function dnsme_records_print_py () { local domain domain_id

domain=$1
if ! domain_id=$(dnsme_domain_id_from_name $domain) ; then
        echo $domain_id
        return 1
fi
echo
echo https://cp.dnsmadeeasy.com/dns/managed/$domain_id
echo
local
export res=$(dnsme_api https://api.dnsmadeeasy.com/V2.0/dns/managed/$domain_id/records)
python << EOF | sort -k 3 | sed 's/$/\n/'
import os,json
data = json.loads(os.environ['res'])
records = data['data']
for record in records:
    name = record['name']
    if name == '':
        name = "@"
    print ('%-11s %-44s %-11s %s' % (record['id'], name, record['type'], record['value'] ))
EOF

} # end function

