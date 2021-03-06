import AppKit
import CoreText
import Quartz

from baseContext import BaseContext

class PDFContext(BaseContext):
    
    fileExtensions = ["pdf"]

    def __init__(self):
        super(PDFContext, self).__init__()
        self._hasContext = False        

    def _newPage(self, width, height):
        self.size(width, height)
        mediaBox = Quartz.CGRectMake(0, 0, self.width, self.height)
        pageInfo = { Quartz.kCGPDFContextMediaBox : mediaBox}

        if self._hasContext:
            # reset the context
            self.reset()
            # add a new page
            Quartz.CGPDFContextEndPage(self._pdfContext)
            Quartz.CGPDFContextBeginPage(self._pdfContext, pageInfo)
        else:
            # create a new pdf document
            self._pdfData = Quartz.CFDataCreateMutable(None, 0)
            dataConsumer = Quartz.CGDataConsumerCreateWithCFData(self._pdfData)
            self._pdfContext = Quartz.CGPDFContextCreate(dataConsumer, mediaBox, None)
            Quartz.CGPDFContextBeginPage(self._pdfContext, pageInfo)
            self._hasContext = True

    def _closeContext(self):
        Quartz.CGPDFContextEndPage(self._pdfContext)
        Quartz.CGPDFContextClose(self._pdfContext)
        self._hasContext = False

    def _saveImage(self, path):
        self._closeContext()
        self._writeDataToFile(self._pdfData, path)
        self._pdfContext = None
        self._pdfData = None

    def _writeDataToFile(self, data, path):
        data.writeToFile_atomically_(path, True)

    def _save(self):
        Quartz.CGContextSaveGState(self._pdfContext)

    def _restore(self):
        Quartz.CGContextRestoreGState(self._pdfContext)

    def _drawPath(self):
        if self._state.path:
            self._save()
            if self._state.shadow is not None:
                self._pdfShadow(self._state.shadow)
                if self._state.gradient is not None:
                    self._save()
                    self._pdfPath(self._state.path)
                    self._state.fillColor = self._state.shadow.color
                    self._state.cmykColor = self._state.shadow.cmykColor
                    self._pdfFillColor()
                    self._state.fillColor = None
                    self._state.cmykColor = None
                    Quartz.CGContextEOFillPath(self._pdfContext)
                    self._restore()
            if self._state.gradient is not None:
                self._save()
                self._clipPath()
                self._pdfGradient(self._state.gradient)
                self._restore()
            elif self._state.fillColor is not None:
                self._pdfPath(self._state.path)
                self._pdfFillColor()
                Quartz.CGContextEOFillPath(self._pdfContext)
            if self._state.strokeColor is not None:
                self._pdfPath(self._state.path)
                self._pdfStrokeColor()
                Quartz.CGContextSetLineWidth(self._pdfContext, self._state.strokeWidth)
                if self._state.lineDash is not None:
                    Quartz.CGContextSetLineDash(self._pdfContext, 0, self._state.lineDash, len(self._state.lineDash))
                if self._state.miterLimit is not None:
                    Quartz.CGContextSetMiterLimit(self._pdfContext, self._state.miterLimit)
                if self._state.lineCap is not None:
                    Quartz.CGContextSetLineCap(self._pdfContext, self._state.lineCap)
                if self._state.lineJoin is not None:
                    Quartz.CGContextSetLineJoin(self._pdfContext, self._state.lineJoin)
                Quartz.CGContextStrokePath(self._pdfContext)
            self._restore()

    def _clipPath(self):
        if self._state.path:
            self._pdfPath(self._state.path)
            Quartz.CGContextEOClip(self._pdfContext)

    def _textBox(self, txt, (x, y, w, h), align):
        attrString = self.attributedString(txt, align=align)
        setter = CoreText.CTFramesetterCreateWithAttributedString(attrString)
        path = Quartz.CGPathCreateMutable()
        Quartz.CGPathAddRect(path, None, Quartz.CGRectMake(x, y, w, h))
        box = CoreText.CTFramesetterCreateFrame(setter, (0, 0), path, None)

        lines = []
            
        ctLines = CoreText.CTFrameGetLines(box)
        for ctLine in ctLines:
            r = CoreText.CTLineGetStringRange(ctLine)
            line = txt[r.location:r.location+r.length]
            while line and line[-1] == " ":
                line = line[:-1]
            lines.append(line.replace("\n", ""))

        origins = CoreText.CTFrameGetLineOrigins(box, (0, len(ctLines)), None)
        for i, (originX, originY) in enumerate(origins):
            line = lines[i]

            self._save()
            Quartz.CGContextSelectFont(self._pdfContext, self._state.text.fontName, self._state.text.fontSize, Quartz.kCGEncodingMacRoman)
            drawingMode = None
            if self._state.shadow is not None:
                self._pdfShadow(self._state.shadow)
                if self._state.gradient is not None:
                    self._save()
                    self._state.fillColor = self._state.shadow.color
                    self._state.cmykColor = self._state.shadow.cmykColor
                    self._pdfFillColor()
                    self._state.fillColor = None
                    self._state.cmykColor = None
                    Quartz.CGContextSetTextDrawingMode(self._pdfContext, kCGTextFill)
                    Quartz.CGContextShowTextAtPoint(self._pdfContext, x+originX, y+originY, line, len(line))
                    self._restore()
            if self._state.gradient is not None:
                self._save()
                Quartz.CGContextSetTextDrawingMode(self._pdfContext, kCGTextClip)
                Quartz.CGContextShowTextAtPoint(self._pdfContext, x+originX, y+originY, line, len(line))
                self._pdfGradient(self._state.gradient)
                self._restore()
                drawingMode = None
            elif self._state.fillColor is not None:
                drawingMode = Quartz.kCGTextFill
                self._pdfFillColor()
            if self._state.strokeColor is not None:
                drawingMode = Quartz.kCGTextStroke
                self._pdfStrokeColor()
                strokeWidth = self._state.strokeWidth
                Quartz.CGContextSetLineWidth(self._pdfContext, self._state.strokeWidth)
                if self._state.lineDash is not None:
                    Quartz.CGContextSetLineDash(self._pdfContext, 0, self._state.lineDash, len(self._state.lineDash))
                if self._state.miterLimit is not None:
                    Quartz.CGContextSetMiterLimit(self._pdfContext, self._state.miterLimit)
                if self._state.lineCap is not None:
                    Quartz.CGContextSetLineCap(self._pdfContext, self._state.lineCap)
                if self._state.lineJoin is not None:
                    Quartz.CGContextSetLineJoin(self._pdfContext, self._state.lineJoin)
            if self._state.fillColor is not None and self._state.strokeColor is not None:
                drawingMode = Quartz.kCGTextFillStroke
            
            if drawingMode is not None:
                Quartz.CGContextSetTextDrawingMode(self._pdfContext, drawingMode)
                Quartz.CGContextShowTextAtPoint(self._pdfContext, x+originX, y+originY, line, len(line))
            self._restore()

    def _image(self, path, (x, y), alpha):
        self._save()
        if path.startswith("http"):
            url = AppKit.NSURL.URLWithString_(path)
        else:
            url = AppKit.NSURL.fileURLWithPath_(path)
        source = Quartz.CGImageSourceCreateWithURL(url, None)
        if source is not None:
            image = Quartz.CGImageSourceCreateImageAtIndex(source, 0, None)
            w = Quartz.CGImageGetWidth(image)
            h = Quartz.CGImageGetHeight(image)
            Quartz.CGContextSetAlpha(self._pdfContext, alpha)
            Quartz.CGContextDrawImage(self._pdfContext, Quartz.CGRectMake(x, y, w, h), image)
        self._restore()

    def _transform(self, transform):
        Quartz.CGContextConcatCTM(self._pdfContext, transform)

    # helpers

    def _pdfPath(self, path):
        path = path.getNSBezierPath()
        for i in range(path.elementCount()):
            instruction, points = path.elementAtIndex_associatedPoints_(i)
            if instruction == AppKit.NSMoveToBezierPathElement:
                Quartz.CGContextMoveToPoint(self._pdfContext, points[0].x, points[0].y)
            elif instruction == AppKit.NSLineToBezierPathElement:
                Quartz.CGContextAddLineToPoint(self._pdfContext, points[0].x, points[0].y)
            elif instruction == AppKit.NSCurveToBezierPathElement:
                Quartz.CGContextAddCurveToPoint(self._pdfContext, points[0].x, points[0].y, points[1].x, points[1].y, points[2].x, points[2].y)
            elif instruction == AppKit.NSClosePathBezierPathElement:
                Quartz.CGContextClosePath(self._pdfContext)

    def _pdfFillColor(self):
        if self._state.cmykFillColor:
            c = self._state.cmykFillColor.getNSObject()
            Quartz.CGContextSetCMYKFillColor(self._pdfContext, c.cyanComponent(), c.magentaComponent(), c.yellowComponent(), c.blackComponent(), c.alphaComponent())
        else:
            c = self._state.fillColor.getNSObject()
            Quartz.CGContextSetRGBFillColor(self._pdfContext, c.redComponent(), c.greenComponent(), c.blueComponent(), c.alphaComponent())
    
    def _pdfStrokeColor(self):
        if self._state.cmykStrokeColor:
            c = self._state.cmykStrokeColor.getNSObject()
            Quartz.CGContextSetCMYKStrokeColor(self._pdfContext, c.cyanComponent(), c.magentaComponent(), c.yellowComponent(), c.blackComponent(), c.alphaComponent())
        else:
            c = self._state.strokeColor.getNSObject()
            Quartz.CGContextSetRGBStrokeColor(self._pdfContext, c.redComponent(), c.greenComponent(), c.blueComponent(), c.alphaComponent())

    def _pdfShadow(self, shadow):
        if shadow.cmykColor:
            c = shadow.cmykColor.getNSObject()
            color = Quartz.CGColorCreateGenericCMYK(c.cyanComponent(), c.magentaComponent(), c.yellowComponent(), c.blackComponent(), c.alphaComponent())
        else:
            c = shadow.color.getNSObject()
            color = Quartz.CGColorCreateGenericRGB(c.redComponent(), c.greenComponent(), c.blueComponent(), c.alphaComponent())

        Quartz.CGContextSetShadowWithColor(self._pdfContext, self._state.shadow.offset, self._state.shadow.blur, color)
    
    def _pdfGradient(self, gradient):
        if gradient.cmykColors:
            colorSpace = Quartz.CGColorSpaceCreateDeviceCMYK()
            colors = []
            for color in gradient.cmykColors:
                c = color.getNSObject()
                cgColor = Quartz.CGColorCreateGenericCMYK(c.cyanComponent(), c.magentaComponent(), c.yellowComponent(), c.blackComponent(), c.alphaComponent())
                colors.append(cgColor)
        else:
            colorSpace = Quartz.CGColorSpaceCreateDeviceRGB()
            colors = []
            for color in gradient.colors:
                c = color.getNSObject()
                cgColor = Quartz.CGColorCreateGenericRGB(c.redComponent(), c.greenComponent(), c.blueComponent(), c.alphaComponent())
                colors.append(cgColor)

        cgGradient = Quartz.CGGradientCreateWithColors(
            colorSpace,
            colors,
            gradient.positions)

        if gradient.gradientType == "linear":
            Quartz.CGContextDrawLinearGradient(self._pdfContext, cgGradient, gradient.start, gradient.end, Quartz.kCGGradientDrawsBeforeStartLocation|Quartz.kCGGradientDrawsAfterEndLocation)
        elif gradient.gradientType == "radial":
            Quartz.CGContextDrawRadialGradient(self._pdfContext, cgGradient, gradient.start, gradient.startRadius, gradient.end, gradient.endRadius, Quartz.kCGGradientDrawsBeforeStartLocation|Quartz.kCGGradientDrawsAfterEndLocation)




