# import the necessary packages
from PIL import Image
import tesserocr;
from tesserocr import PyTessBaseAPI
import cv2
import numpy as np
import os
import re
import ntpath

import ghostscript


import sys
import locale
import ghostscript

args = [
    "ps2pdf", # actual value doesn't matter
    "-dNOPAUSE", "-dBATCH", "-dSAFER",
    "-sDEVICE=png16m",
    "-r300",
    "-q",
    "-sOutputFile=",
    "fileName"
    ]

pathsToMake=[];


# regex shenanigans
splitat=[
    re.compile("^\s*\d\."), # 1. ,2. ,3. etc
    re.compile("^\s*\([a-h]\)"), # (a),(b) etc
    re.compile("^\s*[a-h]\)") # a),b) etc
]


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)




# Get all files that need processing
input_dir="input"
pathsToMake.append(input_dir)
png_dir="pngs"
pathsToMake.append(png_dir)
output_dir="qOut"
pathsToMake.append(output_dir)
junk_dir="junk"
pathsToMake.append(junk_dir)


for i in pathsToMake:
    try:
        os.mkdirs(i)
    except Exception: 
        pass

dirs=os.listdir(input_dir);
for f in dirs:
    # If it is a PDF file:
    if f.split(".")[-1]=="pdf":
        # Run ghostscript to get a png file per page; output to another folder
        # arguments have to be bytes, encode them
        args[-1]=os.path.join(input_dir,f);
        args[-2]="-sOutputFile=" + os.path.join(png_dir,path_leaf(f).split(".")[0]+"page%d.png");
        encoding = locale.getpreferredencoding()
        eargs = [a.encode(encoding) for a in args]
        ghostscript.Ghostscript(*eargs)
dirs=os.listdir(png_dir);

def feedOCR(img):
    with PyTessBaseAPI(path="C:\Program Files (x86)\Tesseract-OCR",lang="eng") as api:
        pil_image = Image.fromarray(img)
        api.SetImage(pil_image)  #  conversion to PIL Image needed for SetImage method  
        result_txt = api.GetUTF8Text()
        return result_txt

for f in dirs:
    image = cv2.imread(os.path.join(png_dir,f))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Make it single channel grayscale. 
    # Go over the image and cut it into bits.
    isAllWhite=True;
    isAQuestion=False;
    lastWhiteIndex=0;
    numQuestions=0;
    lastQuestionStartIndex=0;
    for c,i in enumerate(gray):
        # for each row: 
        # If all white, toggle some state.
        if cv2.mean(np.array(i))[0]==255.0:
            if isAllWhite!=True:
                #print(cv2.mean(np.array(i)))
                isAllWhite=True;
                #cv2.imshow('slice',gray[lastWhiteIndex:c])
                #cv2.waitKey(0)
                #print('processing...')
                text=feedOCR(gray[lastWhiteIndex:c]);
                #print(text)
                # Match the regex
                matched=False;
                for rcnt,regex in enumerate(splitat):
                    if not regex.match(text) is None:
                        matched=True;
                        
                        print (text + " matched " + str(rcnt));
                        break;
                if matched:
                    output=gray[lastQuestionStartIndex:lastWhiteIndex]
                    if isAQuestion:
                        path=output_dir
                    else:
                        path=junk_dir;
                    isAQuestion=True;
                    path=os.path.join(path,path_leaf(f).split(".")[0]+"split"+str(numQuestions)+".png")
                    cv2.imwrite(path,output);
                    numQuestions+=1;
                    lastQuestionStartIndex=lastWhiteIndex;
                lastWhiteIndex=c;
        else:
            #print(cv2.mean(np.array(i)))
            isAllWhite=False;
        if c==len(gray)-1:
            # Write all remaining data to another file.
            output=gray[lastQuestionStartIndex:]
            if isAQuestion:
                path=output_dir;
            else:
                path=junk_dir;
            path=os.path.join(path,path_leaf(f).split(".")[0]+"split"+str(numQuestions)+".png")
            cv2.imwrite(path,output);
            
# load the example image and convert it to grayscale






