#!/bin/bash

#Required when helm state has the old apiversion and velero has restored resources with updated apiversion.
#Since, helm does a 3-way merge, the helm state apiversion should match the desired apiversion.

fix()
{
    secret_name=$1
    namespace=$2
    decoded_state=/tmp/${secret_name}-decode.json
    kubectl -n $namespace get secrets $secret_name -o jsonpath='{.data.release}' | base64 -d | base64 -d | gzip -d > $decoded_state

    #replace apiversion
    sed -i 's#autoscaling/v2beta2#autoscaling/v2#g' $decoded_state
    sed -i 's#policy/v1beta1#policy/v1#g' $decoded_state
    sed -i 's#batch/v1beta1#batch/v1#g' $decoded_state

    gzip -f $decoded_state

    cat $decoded_state.gz | base64 -w0| base64 -w0 > /tmp/${secret_name}-final-release.data

    BASE64_DATA=$(cat /tmp/${secret_name}-final-release.data)

    kubectl patch secret $secret_name -n $namespace --type='json' -p="[{'op': 'replace', 'path': '/data/release', 'value': '${BASE64_DATA}'}]"
}



main()
{
    #all application namespaces
    namespaces=($(kubectl get ns --show-labels | grep team | awk '{print $1}'))

    for ns in ${namespaces[@]}
    do
        #echo $ns
        for revision in  $(helm list -n $ns --no-headers | awk NF | awk 'BEGIN{OFS=".v"} {print $1,$3}')
        do
            secret="sh.helm.release.v1.$revision"
            #echo kubectl get secret -n $ns $secret
            fix $secret $ns
        done
    done
}

main