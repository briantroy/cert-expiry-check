This script checks the expiry date for each of your Certbot (Let's Encrypt) certificates and sends a pushover notification if the cetificate is "near expiry" - with the threshold for near being set in the config json via the "notification_threshold_days".

The script must run with a user privileged to perform "certbot certificates" to list your existing certificates. It currently assumes you have only VALID certificates (no old expired or invalid certs haning around). See certbot delete to clean up your old unused/expired certs.

Usage:
python cert-expiry-check.py <path to your updated sample-config.json>

This script was created as Let's encrypt will no longer (and for good reason) be sending expiry notifications via email. You can learn more about that here:
https://letsencrypt.org/2025/01/22/ending-expiration-emails/
