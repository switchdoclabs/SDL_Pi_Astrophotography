import json, os, re
import paho.mqtt.client as mqtt

from datetime import datetime, timedelta
# from picamera import PiCamera
import picamera
from pytz import timezone
from time import sleep
# from glob import glob
# from shutil import copyfile
from sys import path
from socket import gethostname
from requests import get
from fractions import Fraction
from io import BytesIO
from PIL import Image, ImageDraw, ImageEnhance, ImageFont


def now_str():
	tz = timezone(config['timezone'])
	now = tz.localize(datetime.now())
	now_str = now.strftime(config['datetime_format'])

	return now_str


def on_connect(client, userdata, flags, rc):
    print('MQTT broker connected...')
    client.subscribe(config['mqtt']['topic'], qos=config['mqtt']['qos'])


def on_disconnect(client, userdata, rc):
    print('MQTT broker disconnected...')


def on_subscribe(client, userdata, mid, granted_qos):
    print('MQTT topic subscribed...')


def on_message(client, userdata, msg):
    global capture_flag
    # print(msg.payload)
    reading = json.loads(msg.payload)

    if 'channel' not in reading:
        light = reading['light']
        print('{0}: Light = {1}'.format(now_str(), light))

        if light == 0 and not capture_flag:
            capture_flag = True
            print('{0}: Capture images...'.format(now_str()))
        elif light > 0 and capture_flag:
            capture_flag = False
            print('{0}: Waiting for last light...'.format(now_str()))


def adjust_brightness(image):
    brightness_factor = 100.0
    enhancer = ImageEnhance.Brightness(image)

    image = enhancer.enhance(brightness_factor)

    return image


def adjust_contrast(image):
    contrast_factor = 100.0
    enhancer = ImageEnhance.Contrast(image)

    image = enhancer.enhance(contrast_factor)

    return image


'''def convert_dms_decimal(dms):
	decimal_location = dms['degrees'] + dms['minutes']/60 + dms['seconds']/3600

	if dms['direction'] == 'W' or dms['direction'] == 'S':
		decimal_location *= -1

	return decimal_location


def get_sunrise_sunset(date):
	dec_lat = convert_dms_decimal(config['location']['latitude'])
	dec_long = convert_dms_decimal(config['location']['longitude'])

	url = '{0}lat={1}&lng={2}&date={3}&formatted=0'.format(config['api']['sunrise_sunset_root_url'], dec_lat, dec_long, date)
	# print(url) # debug
	response = get(url)

	if response.status_code == 200:
		data = response.json()

		return {
			'first_light': datetime.fromisoformat(data['results']['civil_twilight_begin']).astimezone(tz),
			'last_light': datetime.fromisoformat(data['results']['civil_twilight_end']).astimezone(tz)
		}
	else:
		return {}

	return response


def get_moon_phase(date):
	return 'something'

	
def get_run_window():
	today = datetime.now()
	tomorrow = datetime.now() + timedelta(days=1)

	today_sunrise_sunset = get_sunrise_sunset(today.strftime('%Y-%m-%d'))
	tomorrow_sunrise_sunset = get_sunrise_sunset(tomorrow.strftime('%Y-%m-%d'))
	# print(today_sunrise_sunset, tomorrow_sunrise_sunset) # debug

	window = {
		'start': today_sunrise_sunset['last_light'],
		'end': tomorrow_sunrise_sunset['first_light']
	}
	
	return window


def calculate_wait(start_dt):
	wait = start_dt - tz.localize(datetime.now())
	
	return int(wait.total_seconds())'''


def run_capture():
	global capture_flag

	# setup the camera
	picamera.PiCamera.CAPTURE_TIMEOUT = 60
	picam = picamera.PiCamera(
		resolution=eval(config['camera']['resolution']),
		framerate=Fraction(1, config['camera']['framerate']),
		sensor_mode=config['camera']['sensor_mode']
	)

	picam.shutter_speed = config['camera']['shutter_speed']
	picam.iso = config['camera']['iso']
	picam.exposure_mode = 'off'

	image_folder = config['images']['capture_dir']
	image_format = config['images']['format']
	image_ext = '.' + image_format

	# open the desired font
	font = ImageFont.truetype(config['images']['text_font'], size=config['images']['text_size'])
	# set the color of image text
	text_color = config['images']['text_color']

	while capture_flag:
		now_ts = now_str()
		# build the file name
		image_file_name = '{0}{1}{2}'.format(image_folder, now_ts, image_ext)
		print(image_file_name)

		# build image stream
		new_image = BytesIO()
		# capture image to stream
		picam.capture(new_image, format=image_format)

		#print('Image captured...')

		# convert image stream to PIL image
		new_image.seek(0)
		raw_image = Image.open(new_image)

		# adjust brightness and contrast of image
		raw_image = adjust_brightness(raw_image)
		raw_image = adjust_contrast(raw_image)

		# add text to PIL image
		draw = ImageDraw.Draw(raw_image)
		draw.text(eval(config['images']['text_location']), now_ts, fill=text_color, font=font)
		
		# write PIL image to file
		raw_image.save(image_file_name)

		'''if tz.localize(datetime.now()) > end_dt:
			loop_flag = False
		else:
			sleep(60)'''
		sleep(60)
	
	picam.close()


# load configuration file
with open('config.json', 'r') as config_file:
	config = json.load(config_file)

hostname = gethostname()
capture_flag = False

# setup the MQTT client
client = mqtt.Client(config['mqtt']['client_name'])
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_subscribe = on_subscribe
client.on_message = on_message

client.connect(
	host=config['mqtt']['host'],
	port=config['mqtt']['port']
)

client.loop_start()

try:
	while True:
		'''
		# get run window
		run_window = get_run_window()

		if tz.localize(datetime.now()) < run_window['start']:
			wait = calculate_wait(run_window['start'])
		elif tz.localize(datetime.now()) >= run_window['start']:
			wait = 0
		
		if wait > 0:
			print('waiting until last light')
			sleep(wait)
		
		run_capture(run_window['end'])
		'''
		run_capture()

		sleep(20)
except KeyboardInterrupt:
	client.loop_stop()
	client.disconnect()