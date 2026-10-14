---
sidebar_navigation:
  title: Backups
  priority: 710
description: Backups in the Enterprise cloud edition.
keywords: backups
---

# Backups

## Data retention policy

Your Enterprise cloud data is continuously backed up and retained for 30 days. Within this period, we can restore your data to any point in time with a precision of 5 minutes if needed.

> [!NOTE]
> Currently, this applies only to cloud instances located in the openproject.com cloud environment.

> [!IMPORTANT]
> At the moment, it is only possible to restore the **entire instance** to a previous state. Any changes made after the restored point will be lost.  
> To help you recover lost information, the restored version will be temporarily available at a separate URL. This allows you to manually transfer the necessary data back to your production instance using **API calls or manual entry**. You will have as much time as needed to complete this process.

## Resource limitations for attachments

In the Enterprise cloud, backups can only include attachments if the total file size of all attachments is less than 1 GB.

If your attachments exceed this limit, please contact us at [support@openproject.com](mailto:support@openproject.com) to manually request a complete backup, which includes an SQL dump with all attachments. Alternatively, consider deleting unused attachments to reduce your data usage below 1 GB.

If the total attachment size exceeds 1 GB, the **Include attachments** checkbox will be disabled, as shown in the screenshot below:

![backup-enterprise-cloud](backup-enterprise-cloud.png)

## Backup via GUI

For detailed instructions on using the Backup feature via the GUI, please refer to the  [System admin guide - Backup page](../../../system-admin-guide/backup/).
