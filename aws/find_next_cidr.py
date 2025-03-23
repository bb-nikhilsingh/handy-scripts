import boto3
import sys
from ipaddress import ip_network, summarize_address_range

def get_vpc_cidr(vpc_id):
    ec2 = boto3.client('ec2')
    response = ec2.describe_vpcs(VpcIds=[vpc_id])
    return response['Vpcs'][0]['CidrBlock']

def get_existing_subnets(vpc_id):
    ec2 = boto3.client('ec2')
    response = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    return [subnet['CidrBlock'] for subnet in response['Subnets']]

def find_next_available_cidr(base_cidr, suffix, existing_cidrs):
    base_network = ip_network(base_cidr)
    existing_networks = [ip_network(cidr) for cidr in existing_cidrs]
    
    for subnet in base_network.subnets(new_prefix=suffix):
        if all(not subnet.overlaps(existing) for existing in existing_networks):
            return subnet
    return None

def main(vpc_id, cidr_suffixes):
    base_cidr = get_vpc_cidr(vpc_id)
    existing_cidrs = get_existing_subnets(vpc_id)
    
    new_cidrs = []
    for suffix in cidr_suffixes:
        next_cidr = find_next_available_cidr(base_cidr, suffix, existing_cidrs)
        if next_cidr:
            print(f"Next available CIDR for /{suffix}: {next_cidr}")
            new_cidrs.append(next_cidr)
            existing_cidrs.append(str(next_cidr))
        else:
            print(f"No available CIDR found for /{suffix}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python find_next_cidr.py <vpc-id> <suffix1> <suffix2> ... <suffixN>")
        sys.exit(1)
    
    vpc_id = sys.argv[1]
    cidr_suffixes = [int(suffix) for suffix in sys.argv[2:]]
    
    main(vpc_id, cidr_suffixes)

