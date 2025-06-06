import json, time, sys                                                                                                                                                                                 
import os.path                                                                                                                                                                                     
from urllib import request
from datetime import date, timedelta
import datetime
import subprocess


def config_reader(config_file):
    """ Reads and validates the config file specified.

    :param config_file: The config file (default or passed in on command line)
    :return: configuration dict - or false if an error occurs.
    """
    if os.path.exists(config_file):
        with open(config_file, 'r') as cfile:
            app_config = json.load(cfile)
        # end with
        return app_config
    else:
        print("The config file: {} does not exist, please try again.".format(config_file))
        return False
    # fin

# end config_reader


def get_config_item(app_config, item):
    """ Gets a specified parameter from the configuration. Nested parameters
     are provided to this function with dot notation e.g., foo.bar.baz

    :param app_config: Configuration dict
    :param item: Dot notation for parameter to return.
    :return:
    """
    item_path = item.split('.')
    this_config = app_config
    for path_part in item_path:
        this_config = this_config[path_part]
    # end For

    return this_config
# end get_config_item


def check_config_file():
    """ validates either the default or command line provided config file.

    :return: Configuration Dict
    """
    # Locate and init config.
    default_config = "config.json"
    if len(sys.argv) == 2:
        # config from command line
        app_config = config_reader(sys.argv[1])
    else:
        # config should be in default
        app_config = config_reader(default_config)
    # fin
    if not app_config:
        print("Exiting due to invalid config file.")
        return False
    # fin
    return app_config
# end check_config_file


def send_pushover_notification(message_content, app_config):
    """
        Sends a notification to the Pushover API.
    :param message_content: The message to send.
    :param app_config: The application configuration.
    :return: The response status code.
    """
    import http.client, urllib
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": get_config_item(app_config, 'pushover_app_token'),
            "user": get_config_item(app_config, 'pushover_user_token'),
            "message": message_content,
        }), { "Content-type": "application/x-www-form-urlencoded" })
    return conn.getresponse().status


# Locate and init config.
app_config = check_config_file()
if not app_config:
    sys.exit()

print("INFO: {} -- Checking Certificates for expiry.".format(datetime.datetime.now()))                                                                                                                                                                                                   
current_time_ts = time.time()                                                                                                                                                                      
local_time = time.ctime(current_time_ts)
date_today = date.today().strftime("%m-%d-%Y")   
date_yesterday = (date.today() - timedelta(days = 1)).strftime("%m-%d-%Y")                                                                                                                                              

cert_result = subprocess.run(['certbot', 'certificates'], capture_output=True, text=True)
certs_info = cert_result.stdout.split("\n")

notification_message = ""

for cert_line in certs_info:
    if "Certificate Name" in cert_line:
        cert_name = cert_line.split(":")[1].strip()
        #print("Cert Name: ", cert_name)

    if "Expiry Date" in cert_line:
        cert_expiry_date = cert_line.split(": ")[1]
        print("Cert Line: ", cert_line)
        print("Cert Expiry Date: ", cert_expiry_date)
        cert_days_remaining = cert_line.split("(VALID: ")[1]
        cert_days_remaining = cert_days_remaining.split(" days)")[0]
        #print("Days remaining {}".format(cert_days_remaining))
        if "VALID" in cert_expiry_date: 
            cert_expiry_date = cert_expiry_date.split(" (VALID: ")[0].replace(" (VALID", "")
            cert_status = "Valid"
            cert_days_remaining = cert_line.split("(VALID: ")[1]
            cert_days_remaining = cert_days_remaining.split(" days)")[0]
        elif "EXPIRED" in cert_expiry_date:
            cert_expiry_date = cert_expiry_date.split(" (EXPIRED: ")[0].replace(" (EXPIRED", "")
            cert_status = "Expired"
            cert_days_remaining = cert_line.split("(EXPIRED: ")[1]
            cert_days_remaining = cert_days_remaining.split(" days)")[0]
        #fin            
        print("Cert Expiry Date: ", cert_expiry_date)
        cert_expiry_date = datetime.datetime.strptime(cert_expiry_date, "%Y-%m-%d %H:%M:%S%z")
        cert_expiry_date_str = cert_expiry_date.strftime("%m-%d-%Y")
        #print("Cert Expiry Date: ", cert_expiry_date_str)

        if cert_status == "Expired":
            cert_message = ("Cert {} has expired on {}.\n".format(cert_name, cert_expiry_date_str))
        elif cert_status == "Valid":
            cert_message = "Cert Expiry Date for {} is: {} (in {} days).\n".format(cert_name, cert_expiry_date_str, cert_days_remaining)
        print(cert_message)

        if int(cert_days_remaining) <= int(get_config_item(app_config, 'notification_threshold_days')):
            print("Cert {} Expiry Date is in {} days or less, sending notification.".format(cert_name, get_config_item(app_config, 'notification_threshold_days')))
            notification_message = notification_message + cert_message
        # end if
    # end if

# end for

if notification_message != "":
    print("Sending notification.")
    send_pushover_notification(notification_message, app_config)

