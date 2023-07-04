import os
import time
import argparse
import sys

try:
    import xlrd
    import xlsxwriter
except ImportError as e:
    print(e)
    raise ImportError(">>> One or more required packages are not properly installed! Run INSTALL_REQUIREMENTS.bat to fix!")

parser = argparse.ArgumentParser(description='Generate Settings File')
parser.add_argument('--g', dest="GenSettings", action="store_true")
parser.add_argument('--d', dest="debugMode", action="store_true")
parser.set_defaults(GenSettings=False, debugMode=False)

GenSettings = (vars(parser.parse_args())["GenSettings"])
debugMode = (vars(parser.parse_args())["debugMode"])


'''----------------------SETTINGS----------------------'''

'''FORMAT ---->   ("Option", "Default", "This is a description"), '''

defaultSettings = [
    ("INV ROWS", "2", "How many rows of equipment you have in your inventory."),
    ("RESOLUTION MODIFIER", "100", "Lower than 100 to lower resolution, greater than 100 to raise resolution. Built in 1440p - Set to 75 for 1080p."),
    ("DEBUG SHOW IMAGE", "No", "Shows the image used for OCR whenever it is captured. Only set to Yes for testing."),
    ("ALTERNATIVE SCREENSHOT", "No", "Turn to Yes to use a multi-monitor screenshot function for testing, or No to use default."),
    ("IMAGE OFFSET", "0", "Use to fine tune OCR accuracy. Increase for bolder text, decrease for less bold. Use with DEBUG SHOW IMAGE to visualize your changes."),
]



def stopBot(err):
    print(">>>>>---------------------------------------------------------------------------<<<<<")
    print(err)
    print(">>>>>----------------------------------------------------------------------------<<<<<")
    time.sleep(3)
    quit()

def intToRoman(num):
    lookup = [
        (1000, 'M'),
        (900, 'CM'),
        (500, 'D'),
        (400, 'CD'),
        (100, 'C'),
        (90, 'XC'),
        (50, 'L'),
        (40, 'XL'),
        (10, 'X'),
        (9, 'IX'),
        (5, 'V'),
        (4, 'IV'),
        (1, 'I'),
    ]
    res = ''
    for (n, roman) in lookup:
        (d, num) = divmod(num, n)
        res += roman * d
    return res


def deformatEntry(inp):
    if isinstance(inp, list):
        toRemove = ["'", '"', "[", "]", "\\", "/"]
        return ''.join(c for c in str(inp) if not c in toRemove)

    elif isinstance(inp, bool):
        if inp:
            return "Yes"
        else:
            return "No"

    else:
        return inp


def writeSettings(sheet, toWrite):

    row = 1  # WRITE SETTINGS
    col = 0
    for col0, col1, col2 in toWrite:
        sheet.write(row, col, col0)
        sheet.write(row, col + 1, col1)
        sheet.write(row, col + 2, col2)
        row += 1


class settingsConfig:
    def __init__(self):
        self.defaultSettings = defaultSettings

    def formatSettingsXlsx(self):
        try:
            with xlsxwriter.Workbook('../Config/Settings.xlsx') as workbook:
                worksheet = workbook.add_worksheet('Settings')
                format = workbook.add_format({'bold': True, 'center_across': True, 'font_color': 'white', 'bg_color': 'gray'})
                boldformat = workbook.add_format({'bold': True, 'center_across': True, 'font_color': 'white', 'bg_color': 'black'})
                lightformat = workbook.add_format({'bold': True, 'center_across': True, 'font_color': 'black', 'bg_color': '#DCDCDC', 'border': True})
                worksheet.set_column(0, 0, 35)
                worksheet.set_column(1, 1, 50)
                worksheet.set_column(2, 2, 130)
                worksheet.write(0, 0, "Option", format)
                worksheet.write(0, 1, "Your Setting", boldformat)
                worksheet.write(0, 2, "Description", format)
                worksheet.set_column('B:B', 50, lightformat)  # END FORMATTING

                writeSettings(worksheet, self.defaultSettings)

        except PermissionError:
            stopBot("Can't open the Settings file. Please close it and make sure it's not set to Read Only.")
        except:
            stopBot("Can't open the Settings file. Please close it and make sure it's not set to Read Only. [0]")



    def reloadSettings(self, tmpSettings):
        for item in tmpSettings:
            for i in enumerate(defaultSettings):
                if (i[1][0]) == item:  # Remove all 'list' elements from the string to feed it back into the speadsheet
                    defaultSettings[i[0]] = (item, deformatEntry(tmpSettings[item]), defaultSettings[i[0]][2])

        self.formatSettingsXlsx()

    def readSettings(self, wb):
        settings = {}
        worksheet = wb.sheet_by_name("Settings")

        for item in range(worksheet.nrows):
            if item == 0:
                pass
            else:
                option = worksheet.cell_value(item, 0)
                try:
                    setting = int(worksheet.cell_value(item, 1))
                except ValueError:
                    setting = str(worksheet.cell_value(item, 1))
                    # Change "Yes" and "No" into bools, only for strings
                    if setting.lower() == "yes":
                        setting = True
                    elif setting.lower() == "no":
                        setting = False

                settings[option] = setting

        if worksheet.nrows != (len(defaultSettings) + 1):
            self.reloadSettings(settings)
            stopBot("The settings have been changed with an update! Please check your Settings.xlsx file then restart the bot.")
        return settings

    def settingsSetup(self):
        global settings

        if not os.path.exists('../Config'):
            print("Creating a Config folder, check it out!")
            os.mkdir("../Config")

        if not os.path.exists('../Config/Settings.xlsx'):
            print("Creating Settings.xlsx")
            self.formatSettingsXlsx()
            stopBot("Please open Config / Settings.xlsx and configure the bot, then run it again.")

        wb = xlrd.open_workbook('../Config/Settings.xlsx')
        # Read the settings file

        settings = self.readSettings(wb)
        return settings


class filterConfig:
    def __init__(self):
        self.defaultSettings = defaultSettings

    def formatFilterXlsx(self):
        try:
            with xlsxwriter.Workbook('../Config/Filter.xlsx') as workbook:
                # Existing 'Filter' sheet creation and formatting
                worksheet_filter = workbook.add_worksheet('Filter')
                format1 = workbook.add_format(
                    {'bold': True, 'center_across': True, 'font_color': 'white', 'bg_color': 'gray'})
                format2 = workbook.add_format(
                    {'bold': True, 'center_across': True, 'font_color': 'black', 'bg_color': '#D3D3D3'})
                boldformat = workbook.add_format(
                    {'bold': True, 'center_across': True, 'font_color': 'white', 'bg_color': 'black'})
                lightformat = workbook.add_format(
                    {'bold': True, 'center_across': True, 'font_color': 'black', 'bg_color': '#DCDCDC', 'border': True})

                toggler = False
                for column in range(1, 15):
                    romanNumeral = intToRoman(column)
                    worksheet_filter.set_column(0, column - 1, 28)
                    if toggler:
                        worksheet_filter.write(0, column - 1, "String to Keep Item - Tier " + str(romanNumeral),
                                               format2)
                        toggler = False
                    else:
                        worksheet_filter.write(0, column - 1, "String to Keep Item - Tier " + str(romanNumeral),
                                               format1)
                        toggler = True

                # New 'Transmute' sheet creation and formatting
                worksheet_transmute = workbook.add_worksheet('Transmute')
                toggler = False
                for column in range(1, 15):
                    romanNumeral = intToRoman(column)
                    worksheet_transmute.set_column(0, column - 1, 28)
                    if toggler:
                        worksheet_transmute.write(0, column - 1, "String to Keep Item - Tier " + str(romanNumeral),
                                                  format2)
                        toggler = False
                    else:
                        worksheet_transmute.write(0, column - 1, "String to Keep Item - Tier " + str(romanNumeral),
                                                  format1)
                        toggler = True

        except PermissionError:
            stopBot("Can't open the Filter file. Please close it and make sure it's not set to Read Only.")
        except:
            stopBot("Can't open the Filter file. Please close it and make sure it's not set to Read Only. [0]")


    def reloadSettings(self, tmpSettings):
        for item in tmpSettings:
            for i in enumerate(defaultSettings):
                if (i[1][0]) == item:  # Remove all 'list' elements from the string to feed it back into the speadsheet
                    defaultSettings[i[0]] = (item, deformatEntry(tmpSettings[item]), defaultSettings[i[0]][2])

        self.formatSettingsXlsx()

    def readFilter(self, wb):
        filterData = {}
        worksheet = wb.sheet_by_name("Filter")
        num_columns = worksheet.ncols  # get the number of columns dynamically
        for column in range(num_columns):
            for item in range(1, worksheet.nrows):  # start from 1 to skip the header
                option = worksheet.cell_value(item, column)
                if option:
                    if str(column) not in filterData:  # create list if it doesn't exist
                        filterData[str(column)] = []
                    filterData[str(column)].append(option)  # append item to the list

        return filterData

    def readTransmute(self, wb):
        transmuteData = {}
        worksheet = wb.sheet_by_name("Transmute")
        num_columns = worksheet.ncols  # get the number of columns dynamically
        for column in range(num_columns):
            for item in range(1, worksheet.nrows):  # start from 1 to skip the header
                option = worksheet.cell_value(item, column)
                if option:
                    if str(column) not in transmuteData:  # create list if it doesn't exist
                        transmuteData[str(column)] = []
                    transmuteData[str(column)].append(option)  # append item to the list

        return transmuteData

    def filterSetup(self):

        if not os.path.exists('../Config'):
            print("Creating a Config folder, check it out!")
            os.mkdir("../Config")

        if not os.path.exists('../Config/Filter.xlsx'):
            print("Creating Filter.xlsx")
            self.formatFilterXlsx()
            stopBot("Please open Config / Filter.xlsx and configure the bot, then run it again.")

        wb = xlrd.open_workbook('../Config/Filter.xlsx')
        # Read the settings file

        filterData = self.readFilter(wb)
        return filterData


def buildConfig():
    if not os.path.exists('../Config'):
        os.mkdir("../Config")

    if not os.path.exists('../Config/Settings.xlsx'):
        print("Creating Settings.xlsx")
        settingsConfig.formatSettingsXlsx(settingsConfig())
        print("\nPlease open Config / Settings.xlsx and configure the bot, then run it again.")
        print("Please follow the setup guide to everything set up! https://rxbots.net/rxbot-setup.html")
        time.sleep(3)
        quit()




if GenSettings:
    buildConfig()