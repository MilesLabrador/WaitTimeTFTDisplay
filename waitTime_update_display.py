#!/usr/bin/python
# Copyright (c) 2014 Adafruit Industries
# Author: Tony DiCola
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
from PIL import Image, ImageOps, ImageDraw, ImageFont
import textwrap
import pymongo
from auth import auth_information
import time

import ILI9341 as TFT
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI


# Raspberry Pi configuration.
DC = 24
RST = 25
SPI_PORT = 0
SPI_DEVICE = 0

# Create TFT LCD display class.
disp = TFT.ILI9341(DC, rst=RST, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=64000000))


def attraction_display(attraction_name=None):
    # Connect to MongoDB databse with realtime attraction information flowing into it
    myclient = pymongo.MongoClient(auth_information['mongodb_url'])
    if attraction_name == None:
        watch_focus = myclient["dlr_attractions"] # If no attraction name is specified, listen to entire database for waitMinutes updates
    else:
        watch_focus = myclient["dlr_attractions"][attraction_name]

    pipeline = [{'$match': {'fullDocument.updates.waitMinutes': {'$exists': 'true'}}}] # watch for updates where the updates dictionary contains key 'waitMinutes', signifying the json has new waitMinutes
    with watch_focus.watch(pipeline) as stream:
        for change in stream:
            print(change)
            print('\n')
            print('waitMinutes for {attraction_name}:'.format(attraction_name=change['fullDocument']['name']), change['fullDocument']['waitMinutes'])
            print('\n')
                            
            display_image = make_waitTime_image(change['fullDocument']['waitMinutes'], change['fullDocument']['name'])
            # Draw the image on the display hardware.
            disp.display(ImageOps.flip(display_image).resize((130, 129)))
            time.sleep(1)

def make_waitTime_image(waitMinutes, attraction_name):
    W,H = (129,130) # Height and width of output image
    image = Image.new('RGB', (W,H), color= 'white') #create base PIL image using white fill
    d = ImageDraw.Draw(image)
    
    # Wrap attraction name around having a max of 15 characters, or whatever fits your display
    max_line_characters = 15
    lines = textwrap.wrap(attraction_name, width=max_line_characters)
    text_height = 0
    attraction_font = ImageFont.truetype("arial.ttf", 15)
    for line in lines:
        width, height = attraction_font.getsize(line)
        d.text(((W - width) / 2, text_height), line, font=attraction_font, fill='navy')
        text_height += height
    
    # Insert waitMinutes at bottom of image
    waitMinutes_text = str(waitMinutes)
    if waitMinutes_text == 'None':
        arial = ImageFont.truetype("arial.ttf", 50)    
    else:
        arial = ImageFont.truetype("arial.ttf", 80)    
    w,h = arial.getsize(waitMinutes_text)
    d.text(((W-w)/2,(H-h)/1.5), waitMinutes_text, font=arial, fill="navy")
    return image

# Initialize display.
disp.begin()
disp.clear()

attraction_display()

