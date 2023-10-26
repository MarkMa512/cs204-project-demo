import subprocess
import openai
import logging

from util.network import match_ip_to_org, to_cidr

# Obtain API key from `key` file stored in the project root directory
openai.api_key = open("key", "r").read().strip('\n')

logger:logging.Logger = logging.getLogger(__name__)

def identify_IXP(ip_address_list: list[str])-> dict[str:str]:

    ip_address_range_dict = {} 
    ixp_list = []

    for ip_address in ip_address_list: 
        logger.info(f"Querying for IP Address: {ip_address} ...")

        # 1. Check if this IP address has already been identified previously 
        result = match_ip_to_org(ip_address_range_dict, ip_address)

        if result != None: 
            # if found to be previous identified 
            logger.info(f"{ip_address} belong to a previously found organizations: {result}")
            logger.info("..................................................")
        else:
            logger.info(f"{ip_address} does not belong to previously found organizations. Run whois command now ...")
            # Step 2: Run the whois command.
            try:
                result = subprocess.check_output(['whois', ip_address], stderr=subprocess.STDOUT).decode('utf-8')
            except subprocess.CalledProcessError as e:
                print(f"Error executing whois on {ip_address}.")
                return {}
            
            # print(result)

            # Step 2: Pass the result of whois to ChatGPT to identify the Regional Registry, Organization, Network Range,and Address
            response = openai.ChatCompletion.create(
                model = "gpt-3.5-turbo",
                messages =[
                    {
                        "role":"user", 
                        "content": f"From the whois details in {result} for ip address {ip_address}, identify the Regional Registry, Network Range, Organization,and Address for {ip_address}. Present the solution in following format:\nRegional Registry:Regional_Registry_Identified\nOrganization:`Organization_identified`\nNetwork Range:`Network_Range_Identified`\nAddress:`Address_Identified",
                    }
                ],
                max_tokens=100
                )

            summary =response['choices'][0]['message']['content']

            # print(summary)


            # # Step 3: Extract necessary information from the summary. 
            regional_registry = None
            network_range = None
            organization = None
            address = None
            
            for line in summary.split('\n'):
                if 'Organization' in line:
                    organization = line.split(':')[-1].strip()
                elif 'Network Range' in line:
                    network_range = line.split(':')[-1].strip()
                elif 'Regional Registry' in line:
                    regional_registry = line.split(':')[-1].strip()
                elif 'Address' in line:
                    address = line.split(':')[-1].strip()

            # convert the network range to CIDR format 
            network_range = to_cidr(network_range)
            # put the newly identified range and org pair into the dictionary 
            ip_address_range_dict[network_range] = organization

            ixp_list.append(
                {
                    'Regional Registry': regional_registry,
                    'Network Range': network_range,
                    'Organization': organization,
                    'Address': address
                }
            )

            logger.info(f"Regional Registry: {regional_registry}")
            logger.info(f"Network Range: {network_range}")
            logger.info(f"Organization:{organization}")
            logger.info(f"Address:{address}")
            logger.info("++++++++++++++++++++++++++++++++++++++++++++++++++")
            
    return ixp_list


# Test
if __name__ == "__main__":
    pass