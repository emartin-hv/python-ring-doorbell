#!/usr/bin/env python3
# Many thanks to @troopermax <https://github.com/troopermax> and tchellomello <https://github.com/tchellomello>
import getpass
import argparse
import time
import datetime
from ring_doorbell import Ring

def get_username():
    try:
        username = raw_input("Username: ")
    except NameError:
        username = input("Username: ")
    return username


def _format_filename(event):
    if not isinstance(event, dict):
        return
    
    local_time = event['created_at'].astimezone()
    event_id = event['id']
    filename = "{}_{}".format(local_time, event_id)

    filename = filename.replace(' ', '_').replace(':', '.')+'.mp4'
    return filename


def main():

    parser = argparse.ArgumentParser(
            description='Ring Doorbell',
            epilog='https://github.com/emartin-pentaho/python-ring-doorbell',
            formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-u',
                        '--username',
                        dest='username',
                        type=str,
                        help='username for Ring account')

    parser.add_argument('-p',
                        '--password',
                        type=str,
                        dest='password',
                        help='username for Ring account')

    parser.add_argument('--devices',
                        action='store_true',
                        default=False,
                        help='list the devices')

    parser.add_argument('--events',
                        action='store_true',
                        default=False,
                        help='list the device events')

    parser.add_argument('--urls',
                        action='store_true',
                        default=False,
                        help='list the download urls')

    parser.add_argument('--download-all',
                        action='store_true',
                        default=False,
                        help='download all videos on your Ring account')

    args = parser.parse_args()

    if not args.username:
        args.username = get_username()

    if not args.password:
        args.password = getpass.getpass("Password: ")

    # connect to Ring account
    myring = Ring(args.username, args.password)
    chimes = myring.chimes 
    doorbells = myring.doorbells
    stickup_cams = myring.stickup_cams 
    devices = list(chimes + doorbells + stickup_cams)

    num_devices = len(devices)

    # Print out device info
    if args.devices:
      print("Number of devices: {}".format(num_devices))
      for device in devices:
        print("Device name: {}".format(device.name))
        print("Device firmware: {}".format(device.firmware))
        print("Device address: {}".format(device.address))
        print("Device battery life: {}".format(device.battery_life))
        print("Device family: {}".format(device.family))
        print("Device timezone: {}".format(device.timezone))
        print("Device latitude: {}".format(device.latitude))
        print("Device longitude: {}\n".format(device.longitude))

    # Shortcut if you only want devices
    need_events = args.events or args.urls or args.download_all
    if (not need_events):
      return

    # Get all device events
    all_device_events = []
    counter = 0
    for device in devices:
      events = []
      history = device.history(limit=100)
      while (len(history) > 0):
        events += history
        counter += len(history)
        history = device.history(older_than=history[-1]['id'])
        all_device_events.append(events)

    # Dump all device events
    if args.events:
      for events in all_device_events:
        motion = len([m['kind'] for m in events if m['kind'] == 'motion'])
        ding = len([m['kind'] for m in events if m['kind'] == 'ding'])
        on_demand = len([m['kind'] for m in events if m['kind'] == 'on_demand'])
        print("Total videos: {}".format(counter))
        print("Ding triggered: {}".format(ding))
        print("Motion triggered: {}".format(motion))
        print("On-Demand triggered: {}\n".format(on_demand))
        for event in events:
          print("Events:")
          print(event)
        print("\n")

    # Print all download URLs
    if args.urls:
      for events in all_device_events:
        for event in events:
          recording_id = event['id']
          url = device.recording_url(recording_id)
          print(url)

    # Download all recording urls
    if args.download_all:
      print("\tDownloading all videos linked on your Ring account.\n" +
            "\tThis may take some time....\n")

      print("\tProcessing and downloading the next {} videos".format(len(events)))

      for events in all_device_events:
        counter = 0
        for event in events:
          counter += 1
          filename = _format_filename(event)
          print("\t{}/{} Downloading {}".format(counter, len(events), filename))

          device.recording_download(event['id'], filename=filename, override=False)


if __name__ == '__main__':
    main()
