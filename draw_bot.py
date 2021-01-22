"""This is a bot used to draw pictures"""
import math
import time
from PIL import Image, ImageGrab
from pynput import mouse, keyboard

SKRIBBLIO = ['1e1e1e', '599bc1', 'ccccc1', '9b591e','ccccab', '7f1e1e', '7fabcc', '1e1e59', '9bc1cc', 'c19b59', '1e1e7f', 'abcccc', 'c1c1c1', 'ccab7f', 'ccc19b', '1e7fab', 'cccccc', 'ab7f1e', '591e1e','1e599b', 'c1cccc', '1d1d1d', '1c1c1c','1b1b1b', '1a1a1a', '191919', '232323', '245195', '133f8c', '9bab9b']  

"""This class is to callibrate the drawer"""
class Calibrator:
    def __init__(self):
        #Stores the position of the last click
        self.last_click = None
        self.origin = None
        self.mouse_listener = mouse.Listener(
            on_click = self.on_click
        )
        self.mouse_listener.start()
        self.controller = mouse.Controller()

    """Called when mouse is clicked"""
    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left and pressed:
            self.last_click = self.controller.position

    """Returns the position of the next click"""
    def next_click(self):
        self.last_click = None
        #Wait until mouse click
        while not self.last_click:
            pass
        return self.last_click

    """Callibrate top drawing rect"""
    def calibrate(self):
        print("Click where you want the top corner of the drawing to be")
        self.origin = self.next_click()

    """Get the palette region"""
    def get_palette_region(self):
        bbox = None
        while bbox is None:
            print("Click palette top left")
            top_left = self.next_click()
            print("Click palette bottom right")
            bottom_right = self.next_click()
            #Check the bbox is valid
            if top_left[0] >= bottom_right[0] or top_left[1] >= bottom_right[1]:
                continue
            bbox = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
        return bbox

    """Calibrate the pallete"""
    def calibrate_palette(self, palette_colors):
        #Configure and grab palette
        bbox = self.get_palette_region()
        im = ImageGrab.grab(bbox)
        #Turn palette colours in to a dict for efficiency
        remaining_colors = {}
        for col in palette_colors:
            remaining_colors[col] = True
        #Maps the colors to its screen position
        color_map = {}
        width = im.size[0]
        i = 0
        for pixel in list(im.getdata()):
            #If all colors found, stop
            if not remaining_colors:
                break
            hex_color = Palette.to_hex(pixel)
            #If color found, store it in map
            if hex_color in remaining_colors:
                rel_y = math.floor(i / width)
                rel_x = i - rel_y * width
                global_pos = (bbox[0] + rel_x, bbox[1] + rel_y)
                #Store in map
                color_map[hex_color] = global_pos 
                #Remove color
                del remaining_colors[hex_color]
            i += 1
        if not remaining_colors:
            print(f"Could not find the following colors {list(remaining_colors.keys())}")
        return color_map

class Palette:
    def __init__(self, palette_map):
        #Maps the colors (hexadecimal) to its position
        self.palette_map = palette_map
        #Stores the closest color map
        self.color_map = {}

    """Converts a hex colour to rgb"""
    @staticmethod
    def to_rgb(hex_color):
        s = hex_color.lstrip('#')
        return (int(s[:2], 16), int(s[2:4], 16), int(s[4:], 16))

    """Pads a hex string with a 0 if too short"""
    @staticmethod
    def pad_hex(hex_str, length):
        while len(hex_str) < length:
            hex_str = '0' + hex_str
        return hex_str

    """Converts rgb tuple to hex string"""
    @staticmethod
    def to_hex(rgb_tup):
        r = Palette.pad_hex(hex(rgb_tup[0])[2:], 2)
        g = Palette.pad_hex(hex(rgb_tup[1])[2:], 2)
        b = Palette.pad_hex(hex(rgb_tup[2])[2:], 2)
        return r + g + b

    """Gets the closest color in the palette"""
    def get_closest_color(self, color):
        #If already stored, return
        if color in self.color_map:
            return self.color_map[color]
        
        #Convert to rgb
        rgb_color = Palette.to_rgb(color)

        #Find the closest colour by distance
        nearest_dist = None
        nearest_color = None
        for p_color in self.palette_map.keys():
            #Convert to rgb tuple
            rgb_p_color = Palette.to_rgb(p_color)
            #Calculate square distance of colour
            r = rgb_p_color[0] - rgb_color[0]
            g = rgb_p_color[1] - rgb_color[1]
            b = rgb_p_color[2] - rgb_color[2]
            dist = r * r + g * g + b * b
            if nearest_dist is None or dist < nearest_dist:
                nearest_dist = dist
                nearest_color = p_color
        #Cache result
        self.color_map[color] = nearest_color
        return nearest_color

    """Change color to the nearest color in the palette"""
    def change_color(self, color, mouse_control):
        p_color = self.get_closest_color(color)
        pos = self.palette_map[p_color]
        mouse_control.position = pos
        mouse_control.click(mouse.Button.left, 1)


"""This draws the drawing"""
class Drawer:
    def __init__(self, origin, controller):
        self.controller = controller
        self.origin = origin
        self.running = True
        self.keyboard_listener = None

    """Rescales pillow image"""
    def rescale(self, img, target_width):
        width = target_width
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
    def draw(self, img, target_width, palette):
        #Rescale image
        img = self.rescale(img, target_width)
        #Convert to RGB
        img = img.convert(mode='RGB')

        width, height = img.size

        self.keyboard_listener = keyboard.Listener(
            on_press = self.on_keypress
        )
        self.keyboard_listener.start()

        i = 0
        last_pixel_color = None
        for pixel in list(img.getdata()):
            #Change color to hex
            hex_color = Palette.to_hex(pixel)
            #Change palette color
            if last_pixel_color != palette.get_closest_color(hex_color):
                palette.change_color(hex_color, self.controller)

            #Click only if its not white
            if pixel != (255,255,255):
                rel_y = math.floor(i / width)
                rel_x = i - rel_y * width
                global_pos = (self.origin[0] + rel_x, self.origin[1] + rel_y)
                self.controller.position = global_pos
                self.controller.click(mouse.Button.left, 0)
            i += 1
            if not self.running:
                break
        self.keyboard_listener.stop()
        print("Finished")

if __name__ == '__main__':
    calib = Calibrator()
    palette_map = calib.calibrate_palette(SKRIBBLIO)
    palette = Palette(palette_map)
    calib.calibrate()
    draw = Drawer(calib.origin, calib.controller)
    #Load image
    im = Image.open('test3.png')
    draw.draw(im, 100, palette)


