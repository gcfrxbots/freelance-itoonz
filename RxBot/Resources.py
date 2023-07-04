from Settings import *
from Initialize import *
import pyautogui
import mss
import mss.tools
import re
import pytesseract
from PIL import Image, ImageOps, ImageGrab
import cv2
import numpy as np
from xlutils.copy import copy
import xlrd
import re
import pygsheets
import random
import pyperclip


pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
pyautogui.FAILSAFE = False  # Might cause nuclear apocalypse

res = settings["RESOLUTION MODIFIER"] / 100

scrollToLineUpBottomDistance = -240
scrollToMoveUpOneBarDistance = -54
timesToScrollUp = 8
portraitOffset = -40

def cvToPil(cvImg):
    cvImg = cv2.cvtColor(cvImg, cv2.COLOR_BGR2RGB)
    pilImg = Image.fromarray(cvImg)
    del cvImg
    return pilImg


def change_contrast(img, level):
    factor = (259 * (level + 255)) / (255 * (259 - level))
    def contrast(c):
        return 128 + factor * (c - 128)
    return img.point(contrast)


def remove_text_before_item_name(text, item_name):
    if item_name not in text:
        return text

    # Split the text using the item_name as the delimiter
    parts = text.split(item_name, 1)

    # Join the parts, effectively removing any text before the item_name
    cleaned_text = item_name + parts[1]

    # Split the cleaned_text into lines, strip leading and trailing spaces, and join them back
    cleaned_lines = [line.strip() for line in cleaned_text.split('\n')]
    lines = list(filter(None, cleaned_lines))[1:]
    #cleaned_text = '\n'.join(cleaned_lines)

    return lines


def extract_item_name(text):
    # Regular expression pattern to match one or more words with at least two characters
    pattern = r'\b\w{2,}\b'

    # Iterate through each line in the text
    for line in text.split('\n'):
        # Find all matches in the current line
        matches = re.findall(pattern, line)

        # Check if there are at least two words in the line
        if len(matches) >= 2:
            # Combine the matched words and return as the item's name
            item_name = ' '.join(matches)
            return item_name

    # If no valid item name is found, return None
    return None



def filter_text(text):
    allowed_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789:+-% '

    # Split the text by newlines
    lines = text.split('\n')

    # Filter each line and join them back with a newline character
    filtered_text = '\n'.join(''.join([char for char in line if char in allowed_chars]) for line in lines)

    return filtered_text



def ocr_image_to_string(pil_image):
    # Resize the image to a larger resolution
    pil_image = pil_image.resize((pil_image.width * 2, pil_image.height * 2), Image.ANTIALIAS)

    # Convert the PIL image to an OpenCV image (numpy array)
    open_cv_image = np.array(pil_image)
    gray_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)

    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray_image, (3, 3), 0)

    # Apply adaptive thresholding
    thresh_image = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 15)

    # Perform OCR on the preprocessed image
    text = pytesseract.image_to_string(thresh_image, config='--psm 6')
    if text:
        filteredText = filter_text(text)

        return filteredText
    else:
        return ""


class resourcesClass:
    def __init__(self):
        self.width, self.height = pyautogui.size()
        self.userText = None
        self.IdText = None
        self.buyInText = None
        self.profitText = None
        self.cachedIdImage = None
        self.handsText = None
        self.lastLeaderboardHandCounts = []
        self.currentLeaderboardHandCounts = []
        self.wipeNextScan = False
        self.oldTempCache = []

    def holdKey(self, key, duration):
        pyautogui.keyDown(key)
        time.sleep(duration)
        pyautogui.keyUp(key)


    def findImageOnScreen(self, imgName, confidence):
        imageLocation = pyautogui.locateOnScreen("Resources/%s" % imgName, confidence=confidence)
        if not imageLocation:
            return False
        #print("Image found at " + str(imageLocation))
        return imageLocation

    def moveMouseToLocation(self, imageLocation):
        x, y = pyautogui.center(imageLocation)
        pyautogui.moveTo(x, y, 0.3)

    def clickImage(self, imgName, confidence=0.85):
        location = self.findImageOnScreen(imgName, confidence)
        if location:
            self.moveMouseToLocation(location)
            time.sleep(0.3)
            pyautogui.click()
            time.sleep(0.3)
            return True
        else:
            return False

    def imgToText(self, img):
        text = pytesseract.image_to_string(img, config='--psm 6')
        #print("OCR TEXT: \n" + text + "\n")
        return text.strip()

    def screenshotRegion(self, left, top, width, height, invert=False, filter=False):
        if settings["ALTERNATIVE SCREENSHOT"]:
            with mss.mss() as sct:
                # The screen part to capture
                region = {'top': top, 'left': left, 'width': width, 'height': height}

                # Grab the data
                sctimg = sct.grab(region)
                img = Image.frombytes("RGB", sctimg.size, sctimg.bgra, "raw", "BGRX")
        else:
            img = pyautogui.screenshot(region=(left, top, width, height))
        newImg = img

        # Upscale
        if filter:
            imgSize = img.size
            img = img.resize((imgSize[0] * 2, imgSize[1] * 2), resample=Image.BOX)

            newImg = img

        if invert:
            img = ImageOps.invert(img)

        if filter == "Normal":
            img = change_contrast(img, 180)

            numpy_image = np.array(img)

            # Convert the numpy array to grayscale using OpenCV
            gray = cv2.cvtColor(numpy_image, cv2.COLOR_BGR2GRAY)

            # Convert the grayscale image back to a PIL image
            pil_gray = Image.fromarray(gray)

            thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)[1]

            result = cv2.GaussianBlur(thresh, (5, 5), 0)
            result = 255 - result

            newImg = cvToPil(result)

        if filter == "Hands":
            img = change_contrast(img, 142)

            cvImg = np.array(img)
            cvImg = cvImg[:, :, ::-1].copy()

            gray = cv2.cvtColor(cvImg, cv2.COLOR_BGR2GRAY)
            revisedCvImg = cv2.fastNlMeansDenoising(gray, cvImg, 67.0, 7, 21)
            (thresh, blackAndWhiteImage) = cv2.threshold(revisedCvImg, (143 + settings["HANDS OFFSET"]), 255, cv2.THRESH_BINARY)
            newImg = cvToPil(blackAndWhiteImage)

        if filter == "ID":
            img = change_contrast(img, 40)

            cvImg = np.array(img)
            cvImg = cvImg[:, :, ::-1].copy()

            gray = cv2.cvtColor(cvImg, cv2.COLOR_BGR2GRAY)
            (thresh, blackAndWhiteImage) = cv2.threshold(gray, 230, 255, cv2.THRESH_BINARY)
            revisedCvImg = cv2.fastNlMeansDenoising(gray, blackAndWhiteImage, 35.0, 7, 5)
            (thresh, blackAndWhiteImage) = cv2.threshold(revisedCvImg, (220 + settings["ID IMAGE OFFSET"]), 255, cv2.THRESH_BINARY)
            newImg = cvToPil(blackAndWhiteImage)

        #newImg.show()



        # thresh = 170
        # fn = lambda x: 255 if x > thresh else 0
        # img = img.convert('L').point(fn, mode='1')


        if settings["DEBUG SHOW IMAGE"]:
            newImg.show()
            print("Showed image, waiting for it to be closed or moved.")
            time.sleep(1)

        #newImg.show()
        return newImg


    def scrollDown(self):
        pyautogui.moveTo(int(resources.width / 2), int(resources.height / 2), 0.3)
        pyautogui.drag(0, int(scrollToMoveUpOneBarDistance * res), 0.8, button="left")
        time.sleep(1.8)


    def scrollUp(self):
        pyautogui.moveTo(int(resources.width / 2), int(resources.height / 2), 0.3)
        pyautogui.drag(0, 400, 0.8, button="left")
        time.sleep(1)




def roman_to_int(s):
    roman_to_int = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    prev_value = 0
    for c in s:
        value = roman_to_int.get(c)
        if value is None:
            return None
        if value > prev_value:
            total += value - 2 * prev_value
        else:
            total += value
        prev_value = value
    return total

def replace_roman_numerals(string):
    roman_regex = r'\b[MDCLXVI]+\b'
    matches = re.finditer(roman_regex, string)
    for match in matches:
        roman_numeral = match.group()
        integer = roman_to_int(roman_numeral)
        if integer is not None:
            string = string.replace(roman_numeral, str(integer))
    return string

def parse_spreadsheet(fromSpreadsheet, ocrTextList, item_tier):
    item_tier = replace_roman_numerals(item_tier)
    fromSpreadsheet = replace_roman_numerals(fromSpreadsheet)

    for ocrText in ocrTextList:
        ocrText = replace_roman_numerals(ocrText)

        # check if the strings are identical
        if fromSpreadsheet == ocrText and fromSpreadsheet >= item_tier:
            return True

        # check if the fromSpreadsheet string contains greater than conditions
        gt_match = re.match(r'>\s*(\d+)%\s*(\w+)', fromSpreadsheet)
        if gt_match:
            gt_value, gt_unit = int(gt_match.group(1)), gt_match.group(2)
            ocr_match = re.match(r'\+(\d+)%\s*(\w+)', ocrText)
            if ocr_match:
                ocr_value, ocr_unit = int(ocr_match.group(1)), ocr_match.group(2)
                if ocr_value >= gt_value and ocr_unit == gt_unit and fromSpreadsheet >= item_tier:
                    return True

        # check if the fromSpreadsheet string is anywhere in the ocrText
        if fromSpreadsheet in ocrText and fromSpreadsheet >= item_tier:
            return True

    # if none of the above conditions are met, return False
    return False



def findTierLevel(x, y):
    pyautogui.moveTo(x, y, 0.2)
    pyautogui.hotkey("F12")
    time.sleep(0.4)
    pyautogui.hotkey("CTRL", "SHIFT", "c")
    time.sleep(0.3)
    pyautogui.moveTo(x, y + 3, 0.2)
    time.sleep(0.1)
    pyautogui.click()
    time.sleep(0.3)
    intValue = 1
    for x in range(3):
        pyautogui.hotkey("Down")
        time.sleep(0.2)
        pyautogui.hotkey("CTRL", "c")
        time.sleep(0.4)
        value = pyperclip.paste()
        if "iQual" in value:
            value = value.split('">')[1]
            value = value.split("<")[0]
            intValue = roman_to_int(value.strip())
            break

    pyautogui.hotkey("F12")
    time.sleep(0.3)
    return intValue


def login():
    resources.clickImage("loginAs.png")
    time.sleep(1)

    if resources.findImageOnScreen("createNewCharacter.png", 0.85):  # We're in the character select screen, pick character
        pyautogui.click(102, 128)
        time.sleep(0.5)
        resources.clickImage("playButton.png")


    resources.clickImage("gotoTown.png")  # Tries to return to town or returns false otherwise
    time.sleep(0.3)



def catacombs():
    while True:  # goes until a fail case is met
        directionKey = random.choice(("w", "a", "s", "d", "w", "w"))

        pyautogui.hotkey(directionKey)
        time.sleep(0.4)

        im = resources.screenshotRegion(232, 135, 600, 600)
        healthbarLocation = None
        try:  # Are we in combat?
            healthbarLocation = pyautogui.locate('Resources/healthbar.png', im, confidence=0.8)
        except:
            pass
        xAdd = 250
        yAdd = 135
        while healthbarLocation:  # Handle multiple mobs
            while healthbarLocation:  # COMBAT
                x = healthbarLocation.left
                y = healthbarLocation.top
                pyautogui.moveTo(x + xAdd, y + yAdd, 0.2)
                # time.sleep(0.2)
                pyautogui.click()
                time.sleep(0.2)
                im = resources.screenshotRegion(232, 135, 600, 600)
                try:
                    healthbarLocation = pyautogui.locate('Resources/healthbar.png', im, confidence=0.8)
                except:
                    break
            # END COMBAT
            time.sleep(0.8)

            if resources.findImageOnScreen("itemDrops.png", 0.8):  # Grab items
                print("Getting item drops...")
                time.sleep(0.5)

                while not resources.findImageOnScreen("emptyItemDrops.png", 0.9):
                    print("Picking item")
                    pyautogui.moveTo(270, 566, 0.1)
                    pyautogui.click()
                    pyautogui.moveTo(470, 566, 0.1)
                    time.sleep(0.5)
                    # Check if inventory is full
                    if resources.findImageOnScreen("inventoryIsFull.png", 0.85):
                        print("INVENTORY IS FULL")
                        return  # DONE WITH CATACOMBS

            pyautogui.press("Space")
            print("Battle complete.")
            time.sleep(0.7)  # BATTLE DONE

        # Return
        pyautogui.hotkey("g")
        time.sleep(0.5)


def levelVitality():
    time.sleep(0.5)
    pyautogui.hotkey("c")
    time.sleep(0.9)
    location = resources.findImageOnScreen("vitality.png", 0.9)
    if location:
        x = location.left
        y = location.top
        pyautogui.moveTo(x+92, y+10, 0.2)
        for x in range(0, 10):
            time.sleep(0.2)
            pyautogui.click()
        time.sleep(0.5)
        print("Vitality level complete, moving to catacombs.")
        pyautogui.press("Space")
    else:
        pyautogui.hotkey("c")
        time.sleep(0.5)
        return


def filterItem(x, y, itemTier, sheet):
    if sheet == "Filter":
        filterData = filterConfig.filterSetup(filterConfig())

        bottomOfBox = resources.findImageOnScreen('ctrlClickItem.png', 0.8)
        if not bottomOfBox:
            return False
        distanceToBottom = (bottomOfBox.top - y)  + 5
        im = resources.screenshotRegion(int(x), int(y),  140, int(distanceToBottom), False)
        #text = resources.imgToText(im)
        text = ocr_image_to_string(im)
        if not text:
            return False

        itemName = extract_item_name(text)
        #print("NAME = " + itemName)
        cleanedText = remove_text_before_item_name(text, itemName)

        # Check if cleaned text fits spreadsheet
        for filterItem in filterData:
            if parse_spreadsheet(filterItem, cleanedText, itemTier):
                return True

    if sheet == "Transmute":
        wb = xlrd.open_workbook('../Config/Filter.xlsx')
        transmuteData = filterConfig.readTransmute(filterConfig(), wb)

        bottomOfBox = resources.findImageOnScreen('ctrlClickItem.png', 0.8)
        if not bottomOfBox:
            return False
        distanceToBottom = (bottomOfBox.top - y) + 5
        im = resources.screenshotRegion(int(x), int(y), 140, int(distanceToBottom), False)
        # text = resources.imgToText(im)
        text = ocr_image_to_string(im)
        if not text:
            return False

        itemName = extract_item_name(text)
        # print("NAME = " + itemName)
        cleanedText = remove_text_before_item_name(text, itemName)

        # Get item tier level

        for x in range(0, 5):
            pyautogui.hotkey("CTRL", "+")  # Zoom in for better image recognition

        pyautogui.hotkey("CTRL", "0")

        # Check if cleaned text fits spreadsheet
        for filterItem in transmuteData:
            if parse_spreadsheet(filterItem, cleanedText, itemTier):
                return True


def deleteItems():  # Looks at each item and deletes the ones that aren't helpful. "The Great Filter"
    pyautogui.hotkey("i")
    # Find the location of the first inventory slot and calculate the rest
    time.sleep(0.5)
    location = resources.findImageOnScreen("equipment.png", 0.85)
    x = location.left + 15
    y = location.top + 25
    for row in range(0, settings["INV ROWS"]):
        for column in range(0,7):
            try:
                pyautogui.moveTo(x, y, 0.2)
                # ITEM FILTERING
                itemTier = findTierLevel(x, y)
                if not itemTier:
                    break
                print("Item Tier " + str(itemTier))
                if not filterItem(x, y, itemTier, "Filter"):  # Trashes all items that are not filtered
                    # Drag item to the traesh
                    pyautogui.click()
                    time.sleep(0.2)
                    pyautogui.mouseDown()
                    time.sleep(0.4)
                    print("Not deleting for testing purposes")
                    #resources.moveMouseToLocation(resources.findImageOnScreen("trash.png", 0.85))
                    time.sleep(0.4)
                    pyautogui.mouseUp()
            except TypeError:
                pass




            x += 45
            # END ITEM FILTERING

        x = location.left + 15
        y += 45 # Move down one



def transmute_and_stabilize():  # Assume this is called with the mouse cursor on the item to be transmuted
    pyautogui.keyDown("Shift")
    time.sleep(0.3)
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.keyUp("Shift")
    time.sleep(0.5)
    transmute = pyautogui.locateOnScreen('Resources/transmute.png', confidence=0.8)  # Start the process
    pyautogui.click(transmute, duration=0.3)
    time.sleep(0.8)
    while True:
        try:
            transmute = pyautogui.locateOnScreen('Resources/transmute.png', confidence=0.8)
            if transmute:
                # Loop for rapid clicking
                for _ in range(10):  # adjust this number based on how rapid you want the clicks to be
                    pyautogui.click(transmute, duration=0.2)  # duration can be adjusted for faster or slower clicks
                    time.sleep(0.1)  # adjust this sleep time for faster or slower clicks


                    bar_filled = pyautogui.locateOnScreen('Resources/barFilled.png', confidence=0.8)
                    if bar_filled:

                        stabilize = pyautogui.locateOnScreen('Resources/stabilize.png', confidence=0.8)
                        if stabilize:
                            pyautogui.click(stabilize, duration=0.25)
                            pyautogui.mouseDown()
                            time.sleep(8)  # holding for 8 seconds now
                            pyautogui.mouseUp()

            else:
                break
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return False

    return True




def transmuteItems():  # Copy of the Delete but to transmute instead

    # Find the location of the first inventory slot and calculate the rest
    time.sleep(0.5)
    location = resources.findImageOnScreen("equipment.png", 0.85)
    x = location.left + 15
    y = location.top + 25
    for row in range(0, settings["INV ROWS"]):
        for column in range(0,7):
            try:
                pyautogui.moveTo(x, y, 0.2)
                # ITEM FILTERING
                itemTier = findTierLevel(x, y)
                if not itemTier:
                    break
                print("Item Tier " + str(itemTier))
                if filterItem(x, y, itemTier, "Transmute"):  # Trashes all items that are not filtered
                    # Drag item to the transmute box
                    pyautogui.click()
                    time.sleep(0.2)
                    pyautogui.mouseDown()
                    x, y = pyautogui.center(resources.findImageOnScreen("transmute.png", 0.85))
                    time.sleep(0.4)
                    resources.moveMouseToLocation((x-30, y-20))
                    time.sleep(0.4)
                    pyautogui.mouseUp()
            except TypeError:
                pass




            x += 45
            # END ITEM FILTERING

        x = location.left + 15
        y += 45 # Move down one


def startTransmuting():
    resetStartAgain()
    time.sleep(0.5)
    resources.clickImage("startTransmuting.png")
    time.sleep(0.5)
    transmuteItems()  # Actually do the transmute thing

def resetStartAgain():
    resources.clickImage("gotoTown.png")
    time.sleep(0.8)
    pyautogui.hotkey("Space")
    time.sleep(0.8)


def startRequest():
    # Before going to catacombs, max vitality


    levelVitality()
    # We start on the main menu. Select the catacombs, or resetStartAgain if no catacombs.


    if not resources.clickImage("selectCatacombs.png"):  # THIS CLICKS THE CATACOMBS
        return  # Resets then tries again

    catacombs()

    # Leave catacombs
    time.sleep(0.5)
    resources.clickImage("gotoTown.png")
    time.sleep(0.3)

    print("Catacombs Done! Filtering items...")

    deleteItems()
    time.sleep(0.5)
    resetStartAgain()
    time.sleep(0.5)
    startTransmuting()





resources = resourcesClass()
