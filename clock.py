#!/usr/bin/env python
import datetime, argparse, time, math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageColor
from rgbmatrix import RGBMatrix, RGBMatrixOptions

timeFmt = '%I:%M:%S%p'
dateFmt = '%b %d %Y'
imageSize = (64,32)
fontHeightStr = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_+='

def setupMatrix():
    options = RGBMatrixOptions()
    options.rows = imageSize[1]
    options.cols = imageSize[0]
    options.chain_length = 1
    options.parallel = 1
    options.gpio_slowdown = 2

    return RGBMatrix(options = options)

def findFonts(searchin):
    foundFonts = ['DejaVuSans.ttf']
    searchPath = os.path.join(searchin, 'fonts')
    if os.path.exists(searchPath):
        fontsInPath = os.listdir(searchPath)
        for fil in fontsInPath:
            tempFile = os.path.join(searchPath, fil)
            if os.path.isfile(tempFile) and tempFile[-4:].lower() == '.ttf':
                foundFonts.append(tempFile)
    foundFonts = [getFontFit(fontName, 16) for fontName in foundFonts]
    return foundFonts

def getFontFit(fontName, fitHeight, startSize=None):
    if startSize is None:
        startSize = 32

    font = ImageFont.truetype(fontName, startSize)
    fontSize = font.getsize(fontHeightStr)
    while fontSize[1] > fitHeight:
        startSize -= 1
        font = ImageFont.truetype(fontName, startSize)
        fontSize = font.getsize(fontHeightStr)
    return font

def rgbFromHue(hue):
    return ImageColor.getrgb('hsv({:d},100%,100%)'.format( hue ))

def genColorTable():
    return [rgbFromHue(col) for col in range(360)]

def genRainbowImage(colorRot, colorTable):
    img = Image.new("RGB", imageSize)
    draw = ImageDraw.Draw(img)
    imgWidth = img.size[0]
    imgHeight = img.size[1]
    for i in range(imgWidth+imgHeight):
        colorInt = (colorRot+i*3)%360
        draw.line(((i-imgHeight, imgHeight), (i, 0)), fill=colorTable[colorInt], width=1)
    return img

def genBlackImage():
    img = Image.new("RGB", imageSize)
    draw = ImageDraw.Draw(img)
    draw.rectangle(((0,0), img.size), fill=(0,0,0))
    return img

def clock(matrix, font, rot, fg, bg):
    now = datetime.datetime.now()
    timStr = now.strftime(timeFmt)
    dateStr = now.strftime(dateFmt)

    timeStrSize = font.getsize(timStr)
    dateStrSize = font.getsize(dateStr)

    alphaImg = Image.new("L", imageSize)
    alphaDraw = ImageDraw.Draw(alphaImg)
    
    if timeStrSize[0] < 64 and dateStrSize[0] < 64:
        # draw it once
        alphaDraw.text((0,0), timStr, font=font, fill=255 )
        alphaDraw.text((0,16), dateStr, font=font, fill=255 )
    else:
        # animate it bouncing left to right
        timeXSiz = timeStrSize[0]
        dateXSiz = dateStrSize[0]
        timeXVar = timeXSiz-64
        dateXVar = dateXSiz-64
        halfTimeX = timeXSiz/2.0
        halfDateX = dateXSiz/2.0

        timeXInc = 0 if timeXVar < 0 else timeXVar
        dateXInc = 0 if dateXVar < 0 else dateXVar

        sinVar = math.sin(rot)

        alphaDraw.text((int(round(sinVar*(timeXInc/2.0)-halfTimeX+32)),0), timStr, font=font, fill=255 )
        alphaDraw.text((int(round(sinVar*(dateXInc/2.0)-halfDateX+32)),16), dateStr, font=font, fill=255 )
    img = Image.composite(fg, bg, alphaImg).convert("RGB")

    matrix.SetImage(img, 0, 0)

def chooseFont(allFonts, currentChoices, debug=None):
    if debug is None:
        debug = False
    font = random.choice(currentChoices)
    currentChoices.remove(font)
    if len(currentChoices) < 1:
        currentChoices.extend(allFonts)
    if debug:
        print('New font: {}'.format(font.getname()))
    return font

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug-fps', action='store_true', help='Enable the performance output')
    parser.add_argument('--debug-font', action='store_true', help='Enable the font output (outputs font name when it changes)')
    args = parser.parse_args()
    matrix = setupMatrix()

    # Loop invariants
    targetFPS = 60
    targetTime = 1/targetFPS
    fontTime = 15*targetFPS

    frameRotAdd = math.pi/(targetFPS*5)
    colorFrameRotAdd = math.pi/(targetFPS*3)

    # Loop variants
    rot = 0
    colorRot = 0
    colorRotDeg = 0
    fontAt = 0

    # Cached data
    colorTable = genColorTable()
    blackImage = genBlackImage()
    rainbowImageTable = [genRainbowImage(rot, colorTable) for rot in range(360)]

    fonts = findFonts(os.path.dirname(os.path.realpath(__file__)))
    fontChoices = fonts.copy()
    font = chooseFont(fonts, fontChoices, debug=args.debug_font)

    while True:
        before = time.time()
        rot = (rot + frameRotAdd) % (math.pi*2)
        colorRot = (colorRot + colorFrameRotAdd) % (math.pi*2)
        colorRotDeg = int( (colorRot/(2*math.pi))*360.0 ) % 360
        fontAt = (fontAt+1) % fontTime
        if fontAt == 0:
            font = chooseFont(fonts, fontChoices, debug=args.debug_font)

        clock(matrix, font, rot, rainbowImageTable[colorRotDeg], blackImage)
        after = time.time()
        consumedTime = after - before
        sleepTime = targetTime-consumedTime
        sleepTime = 0 if sleepTime < 0 else sleepTime
        if args.debug_fps:
            print('Frame time {:.3f} Target {:.3f} Sleep Time {:.3f}'.format(consumedTime, targetTime, sleepTime))
        if sleepTime > 0:
            time.sleep(sleepTime)

if __name__ == '__main__':
    main()
