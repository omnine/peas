__author__ = 'Adam Rutherford'

from twisted.internet import reactor

import eas_client.activesync


def body_result(result, emails, num_emails):

    emails.append(result['Properties']['Body'])

    # Stop after receiving final email.
    if len(emails) == num_emails:
        reactor.stop()


def sync_result(result, fid, actsync, emails):

    assert hasattr(result, 'keys')

    num_emails = len(result.keys())

    for fetch_id in result.keys():

        actsync.add_operation(actsync.fetch, collectionId=fid, serverId=fetch_id,
            fetchType=4, mimeSupport=2).addBoth(body_result, emails, num_emails)


def fsync_result(result, actsync, emails):

    for (fid, finfo) in result.iteritems():
        if finfo['DisplayName'] == 'Inbox':
            actsync.add_operation(actsync.sync, fid).addBoth(sync_result, fid, actsync, emails)
            break


def prov_result(success, actsync, emails):

    if success:
        actsync.add_operation(actsync.folder_sync).addBoth(fsync_result, actsync, emails)
    else:
        reactor.stop()


def extract_emails(creds):

    emails = []

    actsync = eas_client.activesync.ActiveSync(creds['domain'], creds['user'], creds['password'],
            creds['server'], True, device_id=creds['device_id'], verbose=False)

    actsync.add_operation(actsync.provision).addBoth(prov_result, actsync, emails)

    reactor.run()

    return emails
