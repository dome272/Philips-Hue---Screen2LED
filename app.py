import requests
import json
import pyautogui
import cv2
import numpy as np
import math
import argparse
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


class Hue:
    def __init__(self, ip_adress, username):
        self.BASE_URL = "http://" + ip_adress + "/api/" + username
        self.log = requests.get(self.BASE_URL).json()

    def get_num_lights(self):
        return len(self.log["lights"])

    def get_lights(self):
        lights = []
        for light in self.log["lights"]:
            if self.log["lights"][light]["productname"] == "Hue lightstrip plus":
                lights.append(light)
        return lights

    def rgb_to_hue(self, color):
        """
        Code taken from https://stackoverflow.com/a/22649803/10434683
        :param color: list of length 3 with RGB values
        :return: coverted RGB to xy values for LED's
        """
        normalizedToOne = []
        cred = color[0]
        cgreen = color[1]
        cblue = color[2]
        normalizedToOne.append(cred / 255)
        normalizedToOne.append(cgreen / 255)
        normalizedToOne.append(cblue / 255)

        if normalizedToOne[0] > 0.04045:
            red = math.pow((normalizedToOne[0] + 0.055) / (1.0 + 0.055), 2.4)
        else:
            red = normalizedToOne[0] / 12.92

        if normalizedToOne[1] > 0.04045:
            green = math.pow((normalizedToOne[1] + 0.055)
                    / (1.0 + 0.055), 2.4)
        else:
            green = normalizedToOne[1] / 12.92

        if normalizedToOne[2] > 0.04045:
            blue = math.pow((normalizedToOne[2] + 0.055)
                    / (1.0 + 0.055), 2.4)
        else:
            blue = normalizedToOne[2] / 12.92

        X = red * 0.649926 + green * 0.103455 + blue * 0.197109
        Y = red * 0.234327 + green * 0.743075 + blue * 0.022598
        Z = red * 0.0000000 + green * 0.053077 + blue * 1.035763

        x = X / (X + Y + Z)
        y = Y / (X + Y + Z)

        xy = [x, y]
        return xy

    def screen2LED(self):
        all_products = self.get_lights()
        logging.info(f"Following 'Hue lightstrip plus' - products have been found {all_products}.")
        temp_screen = []  # only used to check if the screen changes. If not, the colors don't have to be updated
        while 1:
            screen = np.array(pyautogui.screenshot())  # take screenshot from your screen and convert to numpy array
            if np.array_equal(screen, temp_screen):   # check if screen is the same, if so dont change colors
                continue

            mean_screens = []  # we need to get the mean color of the different part of the screens
            num_lights = len(all_products)
            _split = screen.shape[1] // num_lights  # in my case I have 3 different LED lights (left, middle, right)

            for i in range(num_lights): 
                first_index = _split * i
                second_index = _split * (i + 1)
                temp_screen = screen[:, first_index:second_index, :]  # split the screen in _split parts -> in my case its 3
                mean = [np.mean(temp_screen[:,:,0]), np.mean(temp_screen[:,:,1]), np.mean(temp_screen[:,:,2])]  # take the mean RGB color from every sub-screen
                mean_screens.append(self.rgb_to_hue(mean)) #  convert RGB color to xy

            mean_screens = mean_screens[::-1]  # only for my usecase

            for i in range(len(all_products)):
                requests.put(self.BASE_URL + f"lights/{all_products[i]}/state", f'{{"xy": {mean_screens[i]}}}')  # change the color

            temp_screen = screen


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Python script for making Philips Hue products more fantastic.")
    parser.add_argument("--ip_adress", type=str, help="This is the IP-Adress from your Hue Bridge. More information: Step #2 - https://developers.meethue.com/develop/get-started-2/")
    parser.add_argument("--username", type=str, help="The username registered to the Hue Bridge. More information: https://developers.meethue.com/develop/get-started-2/")
    args = parser.parse_args()
    APP = Hue(args.ip_adress, args.username)
    logging.info("Starting Philips-Hue Screen2LED")
    APP.screen2LED()

