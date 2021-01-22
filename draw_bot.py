"""This is a bot used to draw pictures"""
import math
import time
from PIL import Image
from pynput import mouse, keyboard

class Calibrator:
    def __init__(self):
        self.origin = None
        self.listener = None
        self.controller = mouse.Controller()

    """Called when mouse is clicked"""
    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left and pressed:
            self.origin = self.controller.position

    def callibrate(self):
        self.listener = mouse.Listener(
            on_click = self.on_click
        )
        self.listener.start()
        #Wait until mouse click
        while self.origin is None:
            pass
        self.listener.stop()

class Drawer:
    def __init__(self, origin, img_width, controller):
        self.controller = controller
        self.origin = origin
        self.img_width = img_width
        self.running = True
        self.listener = None

    """Rescales pillow image"""
    def rescale(self, img):
        width = self.img_width
        ratio = img.size[1] / img.size[0]
        height = int(width * ratio)
        img = img.resize((width, height))
        return img

    """Called by keyboard listener"""
    def on_keypress(self, key):
        try:
            if key == keyboard.Key.esc:
                self.running = False
        except:
            pass

    """Draws the given image"""
    def draw(self, img):
        #Rescale image
        img = self.rescale(img)
        #Convert to RGB
        img = img.convert(mode='RGB')
        img = img.convert('1')

        width, height = img.size

        self.listener = keyboard.Listener(
            on_press = self.on_keypress
        )
        self.listener.start()

        i = 0
        for pixel in list(img.getdata()):
            if pixel == 0:
                rel_y = math.floor(i / width)
                rel_x = i - rel_y * width
                global_pos = (self.origin[0] + rel_x, self.origin[1] + rel_y)
                self.controller.position = global_pos
                self.controller.click(mouse.Button.left, 1)
            i += 1
            if not self.running:
                break
        
        self.listener.stop()
        print("Finished")


calib = Calibrator()
calib.callibrate()

#Make drawer
draw = Drawer(calib.origin, 100, calib.controller)
#Load image
im = Image.open('draw.png')

draw.draw(im)