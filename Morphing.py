#! \usr\bin\env python

import numpy as np
from PIL import Image, ImageDraw
import imageio
from scipy.spatial import Delaunay
from scipy.interpolate import RectBivariateSpline
import scipy
import os

class Affine:
    def __init__(self, source, dest):
        if(source.dtype.name != 'float64' or dest.dtype.name != 'float64'):
            raise ValueError('one of the arrays does not contain the elements of correct type')

        if(source.shape != (3,2) or dest.shape != (3,2)):
            raise ValueError('one of the arrays is noe of the correct dimensions')

        self.source = source
        self.destination = dest

        A = np.array([[source[0,0],source[0,1],1,0,0,0],[0,0,0,source[0,0],source[0,1],1],
                          [source[1,0],source[1,1],1,0,0,0],[0,0,0,source[1,0],source[1,1],1],
                          [source[2,0],source[2,1],1,0,0,0],[0,0,0,source[2,0],source[2,1],1]], dtype=np.float64)
        b = np.array([dest[0,0], dest[0,1], dest[1,0], dest[1,1], dest[2,0], dest[2,1]], dtype=np.float64)
        h = np.linalg.solve(A, b);
        self.matrix = np.array([[h[0], h[1], h[2]], [h[3], h[4], h[5]], [0, 0, 1]], dtype=np.float64)
        self.invmatrix = np.linalg.inv(self.matrix)

    def transform(self, sourceImage, destinationImage):
        if not (isinstance(sourceImage, np.ndarray) and isinstance(destinationImage, np.ndarray)):
            raise TypeError('One of the input arguments is not a numpy array')

        x = np.arange(sourceImage.shape[1]) #width/col
        y = np.arange(sourceImage.shape[0]) #heigh/row
        interPolate = RectBivariateSpline(y, x, sourceImage, kx=1, ky=1) #image data is accessed as img[row,col] which is img[y,x]

        maskImg = Image.new('L', (destinationImage.shape[1], destinationImage.shape[0]), 0)
        ImageDraw.Draw(maskImg).polygon(tuple(map(tuple, self.destination)), outline=255, fill=255)
        mask = np.array(maskImg)

        roi = np.transpose(np.nonzero(mask))

        for i,j in roi: #row,col
            tmp1 = self.invmatrix.dot(np.array([[j], [i], [1]]))
            srcX = tmp1[0,0]
            srcY = tmp1[1,0]
            destinationImage[i,j] = (interPolate(srcY, srcX))
            #print('calm down its working {}' .format(destinationImage[i,j]))


        #for i in y: #row/height
        #    for j in x:  #column/width
        #        if mask[i,j] == 255:
        #            tmp1 = self.invmatrix.dot(np.array([[j], [i], [1]]))
        #            srcX = tmp1[0,0]
        #            srcY = tmp1[1,0]
        #            destinationImage[i,j] = interPolate(srcY, srcX)
        #            print('calm down its working {}' .format(destinationImage[i,j]))



        #tmp1 = self.invmatrix.dot(np.array([self.destination[0,0], self.destination[0,1], 1]))
        #tmp2 = self.invmatrix.dot(np.array([self.destination[1,0], self.destination[1,1], 1]))
        #tmp3 = self.invmatrix.dot(np.array([self.destination[2,0], self.destination[2,1], 1]))
        #incomplete

class Blender:
    def __init__(self, startImage, startPoints, endImage, endPoints):
        if not (isinstance(startImage, np.ndarray) and isinstance(startPoints, np.ndarray) and isinstance(endImage, np.ndarray) and isinstance(endPoints, np.ndarray)):
            raise TypeError('One of the input arguments is not a numpy array')

        self.startImage = startImage
        self.startPoints = startPoints
        self.endImage = endImage
        self.endPoints = endPoints
        self.triangles = Delaunay(startPoints)

    def getBlendedImage(self, alpha):
        tmp = self.startImage.shape
        startDest = np.array(Image.new('L', (tmp[1], tmp[0]), 0))
        tmp = self.endImage.shape
        endDest = np.array(Image.new('L', (tmp[1], tmp[0]), 0))

        #targetImage = (1 - alpha)*self.startImage + alpha*self.endImage

        for item in self.triangles.simplices:
            startPts = np.array([[self.startPoints[item[0],0], self.startPoints[item[0], 1]],
                        [self.startPoints[item[1],0], self.startPoints[item[1], 1]],
                        [self.startPoints[item[2],0], self.startPoints[item[2], 1]]], dtype=np.float64)
            endPts = np.array([[self.endPoints[item[0],0], self.endPoints[item[0], 1]],
                      [self.endPoints[item[1],0], self.endPoints[item[1], 1]],
                      [self.endPoints[item[2],0], self.endPoints[item[2], 1]]], dtype = np.float64)
            targetPts = (1 - alpha)*startPts + alpha*endPts
            #targetPts = np.round((1 - alpha)*startPts + alpha*endPts)

            startAffine = Affine(startPts, targetPts)
            startAffine.transform(self.startImage, startDest)
            endAffine = Affine(endPts, targetPts)
            endAffine.transform(self.endImage, endDest)

        blended = np.round((1 - alpha)*startDest + alpha*endDest) #round?

        return blended.astype(np.uint8)
        #return (1 - alpha)*startDest + alpha*endDest

    def generateMorphVideo(self, targetFolderPath, sequenceLength, includeReversed=True):
        if sequenceLength < 10:
            raise ValueError('Sequence Length must be atleast 10')
        try:
            os.stat(targetFolderPath)
        except:
            os.mkdir(targetFolderPath)

        frames = []
        fileNum = 1
        alphas = np.linspace(0.0, 1.0, sequenceLength)
        for a in alphas:
            tmp = self.getBlendedImage(a)
            imageio.imsave('{0}/frame{1:03d}.jpg'.format(targetFolderPath, fileNum), tmp)
            #tmpimg = Image.fromarray(tmp)
            frames.append(tmp)
            fileNum += 1
        
        videoWriter = imageio.get_writer('{0}/morph.mp4'.format(targetFolderPath), fps=5)
        for imgArr in frames:
            videoWriter.append_data(imgArr)
        if includeReversed:
            frames.reverse()
            for imgArr in frames:
                videoWriter.append_data(imgArr)
                imageio.imsave('{0}/frame{1:03d}.jpg'.format(targetFolderPath, fileNum), imgArr)
                fileNum += 1
        videoWriter.close()

class ColorBlender:
    def __init__(self, startImage, startPoints, endImage, endPoints):
        if not (isinstance(startImage, np.ndarray) and isinstance(startPoints, np.ndarray) and isinstance(endImage, np.ndarray) and isinstance(endPoints, np.ndarray)):
            raise TypeError('One of the input arguments is not a numpy array')

        self.startImage = startImage
        self.startPoints = startPoints
        self.endImage = endImage
        self.endPoints = endPoints
        self.triangles = Delaunay(startPoints)

    def getBlendedImage(self, alpha):
        tmp = self.startImage.shape
        startDest = np.array(Image.new('RGB', (tmp[1], tmp[0]), 0))
        tmp = self.endImage.shape
        endDest = np.array(Image.new('RGB', (tmp[1], tmp[0]), 0))

        #targetImage = (1 - alpha)*self.startImage + alpha*self.endImage

        for item in self.triangles.simplices:
            startPts = np.array([[self.startPoints[item[0],0], self.startPoints[item[0], 1]],
                        [self.startPoints[item[1],0], self.startPoints[item[1], 1]],
                        [self.startPoints[item[2],0], self.startPoints[item[2], 1]]], dtype=np.float64)
            endPts = np.array([[self.endPoints[item[0],0], self.endPoints[item[0], 1]],
                      [self.endPoints[item[1],0], self.endPoints[item[1], 1]],
                      [self.endPoints[item[2],0], self.endPoints[item[2], 1]]], dtype = np.float64)
            targetPts = (1 - alpha)*startPts + alpha*endPts
            #targetPts = np.round((1 - alpha)*startPts + alpha*endPts)

            startAffine = ColorAffine(startPts, targetPts)
            startAffine.transform(self.startImage, startDest)
            endAffine = ColorAffine(endPts, targetPts)
            endAffine.transform(self.endImage, endDest)

        blended = np.round((1 - alpha)*startDest + alpha*endDest) #round?

        return blended.astype(np.uint8)
        #return (1 - alpha)*startDest + alpha*endDest

    def generateMorphVideo(self, targetFolderPath, sequenceLength, includeReversed=True):
        if sequenceLength < 10:
            raise ValueError('Sequence Length must be atleast 10')
        try:
            os.stat(targetFolderPath)
        except:
            os.mkdir(targetFolderPath)

        frames = []
        fileNum = 1
        alphas = np.linspace(0.0, 1.0, sequenceLength)
        for a in alphas:
            tmp = self.getBlendedImage(a)
            imageio.imsave('{0}/frame{1:03d}.jpg'.format(targetFolderPath, fileNum), tmp)
            #tmpimg = Image.fromarray(tmp)
            frames.append(tmp)
            fileNum += 1

        videoWriter = imageio.get_writer('{0}/morph.mp4'.format(targetFolderPath), fps=5)
        for imgArr in frames:
            videoWriter.append_data(imgArr)
        if includeReversed:
            frames.reverse()
            for imgArr in frames:
                videoWriter.append_data(imgArr)
                imageio.imsave('{0}/frame{1:03d}.jpg'.format(targetFolderPath, fileNum), imgArr)
                fileNum += 1
        videoWriter.close()

class ColorAffine:
    def __init__(self, source, dest):
        if(source.dtype.name != 'float64' or dest.dtype.name != 'float64'):
            raise ValueError('one of the arrays does not contain the elements of correct type')

        if(source.shape != (3,2) or dest.shape != (3,2)):
            raise ValueError('one of the arrays is noe of the correct dimensions')

        self.source = source
        self.destination = dest

        A = np.array([[source[0,0],source[0,1],1,0,0,0],[0,0,0,source[0,0],source[0,1],1],
                          [source[1,0],source[1,1],1,0,0,0],[0,0,0,source[1,0],source[1,1],1],
                          [source[2,0],source[2,1],1,0,0,0],[0,0,0,source[2,0],source[2,1],1]], dtype=np.float64)
        b = np.array([dest[0,0], dest[0,1], dest[1,0], dest[1,1], dest[2,0], dest[2,1]], dtype=np.float64)
        h = np.linalg.solve(A, b);
        self.matrix = np.array([[h[0], h[1], h[2]], [h[3], h[4], h[5]], [0, 0, 1]], dtype=np.float64)
        self.invmatrix = np.linalg.inv(self.matrix)

    def transform(self, sourceImage, destinationImage):
        if not (isinstance(sourceImage, np.ndarray) and isinstance(destinationImage, np.ndarray)):
            raise TypeError('One of the input arguments is not a numpy array')

        x = np.arange(sourceImage.shape[1]) #width/col
        y = np.arange(sourceImage.shape[0]) #heigh/row

        maskImg = Image.new('L', (destinationImage.shape[1], destinationImage.shape[0]), 0)
        ImageDraw.Draw(maskImg).polygon(tuple(map(tuple, self.destination)), outline=255, fill=255)
        mask = np.array(maskImg)
        roi = np.transpose(np.nonzero(mask))

        srcTranspose = np.transpose(sourceImage)

        interPolateR = RectBivariateSpline(y, x, np.transpose(srcTranspose[0]), kx=1, ky=1) #image data is accessed as img[row,col] which is img[y,x]
        interPolateG = RectBivariateSpline(y, x, np.transpose(srcTranspose[1]), kx=1, ky=1) #image data is accessed as img[row,col] which is img[y,x]
        interPolateB = RectBivariateSpline(y, x, np.transpose(srcTranspose[2]), kx=1, ky=1) #image data is accessed as img[row,col] which is img[y,x]

        for i,j in roi: #row,col
            tmp1 = self.invmatrix.dot(np.array([[j], [i], [1]]))
            srcX = tmp1[0,0]
            srcY = tmp1[1,0]
            destinationImage[i,j,0] = (interPolateR(srcY, srcX))
            destinationImage[i,j,1] = (interPolateG(srcY, srcX))
            destinationImage[i,j,2] = (interPolateB(srcY, srcX))

if __name__=="__main__":
    img = imageio.imread('me.jpg')
    startImage = np.array(img)
    startPoints = np.loadtxt('me.jpg.txt')
    #print(Delaunay(startPoints).simplices[19])
    img = imageio.imread('jen.jpg')
    endImage = np.array(img)
    endPoints = np.loadtxt('jen.jpg.txt')
    #print(Delaunay(endPoints).simplices[19])
    tmp = ColorBlender(startImage, startPoints, endImage, endPoints)

    #print(tmp.triangles.simplices[0])
    #tmp2 = Image.fromarray(tmp.getBlendedImage(0.5))
    #tmp2.show()

    #tmp2 = tmp.getBlendedImage(0.5)
    #imageio.imsave('pms.jpg', tmp2)
    tmp.generateMorphVideo('morphResults', 20)

    #tmp2 = tmp.getBlendedImage(0.1)
    #imageio.imsave('t01.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.2)
    #imageio.imsave('t02.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.3)
    #imageio.imsave('t03.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.4)
    #imageio.imsave('t04.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.5)
    #imageio.imsave('t05.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.6)
    #imageio.imsave('t06.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.7)
    #imageio.imsave('t07.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.8)
    #imageio.imsave('t08.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.9)
    #imageio.imsave('t09.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(1)
    #imageio.imsave('t10.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.9)
    #imageio.imsave('t11.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.8)
    #imageio.imsave('t12.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.7)
    #imageio.imsave('t13.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.6)
    #imageio.imsave('t14.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.5)
    #imageio.imsave('t15.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.4)
    #imageio.imsave('t16.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.3)
    #imageio.imsave('t17.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.2)
    #imageio.imsave('t18.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0.1)
    #imageio.imsave('t19.jpg', tmp2)
    #tmp2 = tmp.getBlendedImage(0)
    #imageio.imsave('t20.jpg', tmp2)


    #img = imageio.imread('test3.jpg')
    #startImage = np.array(img)
    #startImage = tmp2

    #img = imageio.imread('frame021.png')
    #endImage = np.array(img)

    #tmp = np.absolute(endImage - startImage)
    #nonzeros = np.transpose(np.nonzero(tmp))

    #testOut = np.array(Image.new('L', (800, 600), 0))
    #for i,j in nonzeros:
    #    testOut[i,j] = 255
    #
    #imageio.imsave('pt7.jpg', testOut)
