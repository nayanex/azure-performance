#!/usr/bin/env python2
"""
Stops Azure resource manager virtual machines in a subscription.

This Azure Automation runbook runs on Azure to stop (deallocate) Azure VMSSs in a subscription.
If no arguments are specified, then all VMSSs that are currently started are stopped.
If a resource group is specified, then all VMSSs in the resource group are stopped.
If a resource group and VMSS are specified, then that specific VMSS is stopped.

Args:
    groupname (-g) - Resource group name.
    vmssname (-v) - virtual machine name

    Stops the virtual machines
    Example 1:
            stop_azure_vmss.py -g <resourcegroupname> -v <vmssname>
            stop_azure_vmss.py -g <resourcegroupname>
            stop_azure_vmss.py

Changelog:
    2017-09-11 AutomationTeam:
    -initial script

https://docs.microsoft.com/en-us/python/api/azure-mgmt-compute/azure.mgmt.compute.computemanagementclient?view=azure-python
"""
import threading
import getopt
import sys
import azure.mgmt.resource
import azure.mgmt.storage
import azure.mgmt.compute
import automationassets
import OpenSSL
from msrestazure import azure_active_directory
import adal

# Max number of VMSSs to process at a time
_MAX_THREADS = 20

# Returns a credential based on an Azure Automation RunAs connection dictionary
def get_automation_runas_credential(runas_connection):
    """Returs a credential that can be used to authenticate against Azure resources"""
    # Get the Azure Automation RunAs service principal certificate
    cert = automationassets.get_automation_certificate("AzureRunAsCertificate")
    sp_cert = OpenSSL.crypto.load_pkcs12(cert)
    pem_pkey = OpenSSL.crypto.dump_privatekey(
        OpenSSL.crypto.FILETYPE_PEM, sp_cert.get_privatekey()
    )

    # Get run as connection information for the Azure Automation service principal
    application_id = runas_connection["ApplicationId"]
    thumbprint = runas_connection["CertificateThumbprint"]
    tenant_id = runas_connection["TenantId"]

    # Authenticate with service principal certificate
    resource = "https://management.core.windows.net/"
    authority_url = "https://login.microsoftonline.com/" + tenant_id
    context = adal.AuthenticationContext(authority_url)
    return azure_active_directory.AdalAuthentication(
        lambda: context.acquire_token_with_client_certificate(
            resource, application_id, pem_pkey, thumbprint
        )
    )


class StopVMSSThread(threading.Thread):
    """Thread class to stop Azure VMSS"""

    def __init__(self, resource_group, vmss_name):
        threading.Thread.__init__(self)
        self.resource_group = resource_group
        self.vmss_name = vmss_name

    def run(self):
        print(
            "Stopping " + self.vmss_name + " in resource group " + self.resource_group
        )
        sys.stdout.flush()
        stop_vmss(self.resource_group, self.vmss_name)
        print("Stopped " + self.vmss_name + " in resource group " + self.resource_group)
        sys.stdout.flush()


def stop_vmss(resource_group, vmss_name):
    """Stops a vm in the specified resource group"""
    # Stop the VMSS
    vmss_stop = compute_client.virtual_machine_scale_set_vms_vms.begin_deallocate(
        resource_group, vmss_name
    )
    vmss_stop.wait()


# Process any arguments sent in
resource_group_name = None
vmss_name = None

opts, args = getopt.getopt(sys.argv[1:], "g:v:")
for o, a in opts:
    if o == "-g":  # if resource group name is passed with -g option then take it
        resource_group_name = a
    elif o == "-v":  # if vm name is mentioned after script name with -v then read it
        vmss_name = a

# Check for correct arguments passed in
if vmss_name is not None and resource_group_name is None:
    raise ValueError("VMSS argument passed in without a resource group specified")

# Authenticate to Azure using the Azure Automation RunAs service principal
automation_runas_connection = automationassets.get_automation_connection(
    "AzureRunAsConnection"
)
azure_credential = get_automation_runas_credential(automation_runas_connection)
subscription_id = str(automation_runas_connection["SubscriptionId"])

resource_client = azure.mgmt.resource.ResourceManagementClient(
    azure_credential, subscription_id
)

compute_client = azure.mgmt.compute.ComputeManagementClient(
    azure_credential, subscription_id
)

# Get list of resource groups
groups = []
if resource_group_name is None and vmss_name is None:
    # Get all resource groups
    groups = resource_client.resource_groups.list()
elif resource_group_name is not None and vmss_name is None:
    # Get specific resource group
    resource_group = resource_client.resource_groups.get(resource_group_name)
    groups.append(resource_group)
elif resource_group_name is not None and vmss_name is not None:
    # Specific resource group and VMSS name passed in so stop the VMSS.
    vmss_detail = compute_client.virtual_machine_scale_set_vms.get(
        resource_group_name, vmss_name, expand="instanceView"
    )
    if vmss_detail.get_instance_view.statuses[1].code == "PowerState/running":
        stop_vmss(resource_group_name, vmss_name)

# List of threads that are used to Stop VMSSs in parallel
vmss_threads_list = []

# Process any VMs that are in a group
for group in groups:
    vmss_list = compute_client.virtual_machine_scale_set_vms.list(group.name, "udacity-vmss")
    for vmss in vmss_list:
        vmss_detail = compute_client.virtual_machine_scale_sets.get(
            group.name, vmss.name, expand="instanceView"
        )
        
        if vmss.instance_view.statuses[1].code == "PowerState/running":
            stop_vmss_thread = StopVMSSThread(group.name, vmss.name)
            stop_vmss_thread.start()
            vmss_threads_list.append(stop_vmss_thread)
            if len(vmss_threads_list) > _MAX_THREADS:
                for thread in vmss_threads_list:
                    thread.join()
                del vmss_threads_list[:]

# Wait for all threads to complete
for thread in vmss_threads_list:
    thread.join()

print("Finished stopping all VMSSs")
