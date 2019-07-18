import cv2
from videocaptureasync import VideoCaptureAsync
import imutils
import numpy as np
from imutils.object_detection import non_max_suppression
import pytesseract
from pytesseract import Output
import re
import difflib

layerNames = [
    "feature_fusion/Conv_7/Sigmoid",
    "feature_fusion/concat_3"]

net = cv2.dnn.readNet('frozen_east_text_detection.pb')
min_confidence = 0.99

def levenshtein_ratio_and_distance(s, t, ratio_calc = True):
    """ levenshtein_ratio_and_distance:
        Calculates levenshtein distance between two strings.
        If ratio_calc = True, the function computes the
        levenshtein distance ratio of similarity between two strings
        For all i and j, distance[i,j] will contain the Levenshtein
        distance between the first i characters of s and the
        first j characters of t
    """
    # Initialize matrix of zeros
    rows = len(s)+1
    cols = len(t)+1
    distance = np.zeros((rows,cols),dtype = int)

    # Populate matrix of zeros with the indeces of each character of both strings
    for i in range(1, rows):
        for k in range(1,cols):
            distance[i][0] = i
            distance[0][k] = k

    # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions    
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row-1] == t[col-1]:
                cost = 0 # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
            else:
                # In order to align the results with those of the Python Levenshtein package, if we choose to calculate the ratio
                # the cost of a substitution is 2. If we calculate just distance, then the cost of a substitution is 1.
                if ratio_calc == True:
                    cost = 2
                else:
                    cost = 1
            distance[row][col] = min(distance[row-1][col] + 1,      # Cost of deletions
                                 distance[row][col-1] + 1,          # Cost of insertions
                                 distance[row-1][col-1] + cost)     # Cost of substitutions
    if ratio_calc == True:
        # Computation of the Levenshtein Distance Ratio
        print(s, t)
        Ratio = ((len(s)+len(t)) - distance[row][col]) / (len(s)+len(t))
        return Ratio
    else:
        # print(distance) # Uncomment if you want to see the matrix showing how the algorithm computes the cost of deletions,
        # insertions and/or substitutions
        # This is the minimum number of edits needed to convert string a to string b
        return distance[row][col]

def decode_predictions(scores, geometry):
    # grab the number of rows and columns from the scores volume, then
    # initialize our set of bounding box rectangles and corresponding
    # confidence scores
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []
 
    # loop over the number of rows
    for y in range(0, numRows):
        # extract the scores (probabilities), followed by the
        # geometrical data used to derive potential bounding box
        # coordinates that surround text
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]
 
        # loop over the number of columns
        for x in range(0, numCols):
            # if our score does not have sufficient probability,
            # ignore it
            if scoresData[x] < min_confidence:
                continue
 
            # compute the offset factor as our resulting feature
            # maps will be 4x smaller than the input image
            (offsetX, offsetY) = (x * 4.0, y * 4.0)
 
            # extract the rotation angle for the prediction and
            # then compute the sin and cosine
            angle = anglesData[x]
            cos = np.cos(angle)
            sin = np.sin(angle)
 
            # use the geometry volume to derive the width and height
            # of the bounding box
            h = xData0[x] + xData2[x]
            w = xData1[x] + xData3[x]
 
            # compute both the starting and ending (x, y)-coordinates
            # for the text prediction bounding box
            endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
            endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
            startX = int(endX - w)
            startY = int(endY - h)
 
            # add the bounding box coordinates and probability score
            # to our respective lists
            rects.append((startX, startY, endX, endY))
            confidences.append(scoresData[x])
 
    # return a tuple of the bounding boxes and associated confidences
    return (rects, confidences)

class cv_card_reader:
    config = ("-l eng --oem 1 --psm 9")

    def __init__(self):
        self.cap = VideoCaptureAsync(0)
        self.cap.start()
        self.regex = re.compile('[^a-z]')

    def close(self):
        self.cap.stop()

    def grab_text(self, show = False):
        text_buffer = []
        while True:
            _, orig = self.cap.read()
            if orig.shape[0] == 720: orig = orig[:704]
            frame = cv2.resize(orig, (int(480),int(320)))
            H, W = orig.shape[:2]
            blob = cv2.dnn.blobFromImage(frame, 1.0, (480, 320),
                (123.68, 116.78, 103.94), swapRB=True, crop=False)
            net.setInput(blob)
            (scores, geometry) = net.forward(layerNames)
            (rects, confidences) = decode_predictions(scores, geometry)
            boxes = non_max_suppression(np.array(rects), probs=confidences)
            if len(boxes) > 0:
                boxes = np.array(sorted(boxes, key = lambda x: x[0] + x[1])).astype(np.float)
                if show:
                    for j in boxes:
                        startX, startY, endX, endY = [int(i) for i in j]
                        cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 0, 255), 2)
                boxes[:,0] *= W/480
                boxes[:,2] *= W/480
                boxes[:,1] *= H/320
                boxes[:,3] *= H/320
                boxes[:,0] -= 10 * 2
                boxes[:,1] -= 15 * 2
                boxes[:,2] += 10 * 2
                boxes[:,3] += 15 * 2
                counter = 1
                while True:
                    if len(boxes) < counter + 1: break
                    if boxes[0][0] > boxes[counter][2] or boxes[0][2] < boxes[counter][0]: break
                    if boxes[0][1] > boxes[counter][3] or boxes[0][3] < boxes[counter][1]: break
                    for i in range(2): boxes[0][i] = min(boxes[0][i], boxes[counter][i])
                    for i in range(2,4): boxes[0][i] = max(boxes[0][i], boxes[counter][i])
                    counter += 1

                boxes[:,0] += 10
                boxes[:,1] += 15
                boxes[:,2] -= 10
                boxes[:,3] -= 15
                for i in range(4):
                    max_value = H if i % 2 else W
                    boxes[0][i] = min(max(boxes[0][i], 0), max_value)
                startX, startY, endX, endY = [int(i) for i in boxes[0]]
                crop_img = orig[startY:endY, startX:endX]
                if show: cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)
                # text = pytesseract.image_to_string(crop_img, config=self.config)
                data = pytesseract.image_to_data(crop_img, config=self.config, output_type=Output.DICT)
                text = ""
                for i in range(len(data["conf"])):
                    if int(data['conf'][i]) > 50: text += data['text'][i]
                text = self.regex.sub('', text.lower())
                if len(text) == 0: continue
                text_buffer.append(text)
            if show:
                cv2.imshow('img', orig)
                cv2.waitKey(1)
            if len(text_buffer) >= 2:
                print(len(text_buffer))
                ratio = levenshtein_ratio_and_distance(text_buffer[-1], difflib.get_close_matches(text_buffer[-1], text_buffer)[0])
                if ratio > 0.8:
                    if not show: return text_buffer[-1]
                    print(text_buffer[-1])
                    text_buffer = []
                # text_buffer.pop(0)

if __name__ == '__main__':
    card_reader = cv_card_reader()
    text = card_reader.grab_text(show=True)
    print(text)
    card_reader.close()



