# Rotas relacionadas ao usuário

from typing import Annotated
from fastapi import FastAPI, File, UploadFile, Form
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from ..service.sighting_service import SightingService
from ..schema.sighting_schema import SightingCreate, Sighting, Response, FileCreate, SightingFile, SightingForm, FileUpdate
from ..utils.config import get_async_session
from pathlib import Path
from typing import List

import os
import json
import requests

import cv2
import numpy as np
import os
import sys

#CONFIDENCE = 0.82 
#SCORE_THRESHOLD = 0.5
#IOU_THRESHOLD = 0.5 


#alterado para identificar mais peixes
CONFIDENCE = 0.6 
SCORE_THRESHOLD = 0.5
IOU_THRESHOLD = 0.5

labels = ['Fish']
color = [0,0,255]
colors = [[0,0,255]]

WIDTH = 608
HEIGHT = 608

config_path = "E:\\YOLO\\Yolo-Fish-Files\\cfg\\yolov4.cfg"
weights_path = "E:\\YOLO\\Yolo-Fish-Files\\weights\\merge_yolov4.weights"

#config_path = "E:\\YOLO\\Yolo-Fish-Files\\cfg\\yolov4-tiny.cfg"
#weights_path = "E:\\YOLO\\Yolo-Fish-Files\\weights\\yolov4-tiny.weights"


net = cv2.dnn.readNetFromDarknet(config_path, weights_path)

out_path = 'E:\\YOLO\\Saida_Exemplos\\'

service_url = 'http://localhost:5000/classify_inception'
#service_url = 'http://localhost:5000/classify_vgg'

router = APIRouter(prefix="/sightings", tags=['Sighting'])

UPLOAD_DIR = Path("sightings")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=Response)
async def submit_sighting(latitude: Annotated[str, Form()], longitude: Annotated[str, Form()], file_uploads: list[UploadFile], db: AsyncSession = Depends(get_async_session)):
    
    #try:
        # Create sighting
        sighting_data = SightingCreate(latitude=latitude, longitude=longitude, status='PROCESSANDO')
        print("============== antes create_sighting ===========")
        print(sighting_data)
        sighting = await SightingService.create_sighting(db, sighting_data)
        sighting_id = sighting.id
        print("============== depois create_sighting ===========")
        # Upload files and create sighting files
        notFishDetected = 0
        for file in file_uploads:
            save_to = UPLOAD_DIR / file.filename
            # Save file to disk
            with save_to.open("wb") as buffer:
                buffer.write(file.file.read())
                
            #YOLO
            img = get_fish_segmentation(os.path.join(UPLOAD_DIR,file.filename))
            
            if img == 1:         
                # Create sighting file record in the database
                file_data = FileCreate(name=file.filename, path=str(save_to), sighting_id=sighting_id, status='PROCESSANDO')
                sighting_file = await SightingService.create_sighting_file(db, file_data)
                sighting_file_id = sighting_file.id
                
                # Call ML Model - input will be filename
                print("========= call ml ANTES ==========")
                serialized = json.dumps(os.path.join(os.getcwd(), save_to))
            
                # Original - ML results
                response_ml = requests.post(url=service_url, data=serialized, headers={'content_type':'application/json'})
                ml_result = response_ml.content
                print(str(response_ml.content))
                print("========= call ml DEPOIS ==========")
                
                # Update sighting file results in the database
                print("========= update_sighting_file ANTES ==========")
                print(ml_result)
                file_update_data = FileUpdate(status='CONCLUÍDO', ml_class_result=ml_result)
                await SightingService.update_sighting_file(db, sighting_file_id, file_update_data)
                print("========= update_sighting_file DEPOIS ==========")
            else:
                notFishDetected = notFishDetected + 1
               
        if notFishDetected == len(file_uploads):
            return Response(detail="Avistamento não cadastrado! Imagens inválidas.", result= 2)
        elif notFishDetected > 0:
            return Response(detail="Avistamento cadastrado, mas algumas imagens inválidas foram descartadas.", result= 1)
        else:        
            return Response(detail="Avistamento cadastrado com sucesso!", result= 0)
    
    #except Exception as e:
        #raise HTTPException(status_code=500, detail="Erro ao cadastrar avistamento.")

@router.get("/sightings", response_model=list[Sighting])
async def read_sightings(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_session)):
    sightings = await SightingService.get_sightings(db, skip=skip, limit=limit)
    return sightings


@router.get("/files", response_model=list[SightingFile])
async def read_sightings_files(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_async_session)):
    sightings_files = await SightingService.get_sightings_files(db, skip=skip, limit=limit)
    return sightings_files

@router.get("/files/{sighting_id}", response_model=list[SightingFile])
async def read_user(sighting_id: int, db: AsyncSession = Depends(get_async_session)):
    sightings_files = await SightingService.get_sightings_files_by_sighting_id(db, sighting_id)
    return sightings_files

@router.get("/sightings/images/{file_id}")
async def get_image(file_id: int, db: AsyncSession = Depends(get_async_session)):
    sightings_file = await SightingService.get_file_by_id(db, file_id)
    filename = sightings_file.name
    print(filename)
    file_path = UPLOAD_DIR / filename
    print(file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path)


def get_fish_segmentation(filepath):
    image = cv2.imread(filepath)
    file_name = os.path.basename(filepath)
    filename, ext = file_name.split(".")
    #print(CONFIDENCE)
    isFish = 0

    h, w = image.shape[:2]
    blob = cv2.dnn.blobFromImage(image, 1/255.0, (WIDTH, HEIGHT), swapRB=True, crop=False)

    net.setInput(blob)

    ln = net.getLayerNames()
    try:
        ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    except IndexError:
        # in case getUnconnectedOutLayers() returns 1D array when CUDA isn't available
        ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

    layer_outputs = net.forward(ln)

    font_scale = 3
    thickness = 3
    boxes, confidences, class_ids = [], [], []
    # loop over each of the layer outputs
    for output in layer_outputs:
        # loop over each of the object detections
        for detection in output:
            # extract the class id (label) and confidence (as a probability) of
            # the current object detection
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            # discard out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            # print("==========  confidence =========")
            # print(confidence)
            if confidence > CONFIDENCE:
                # scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[:4] * np.array([w, h, w, h])
                (centerX, centerY, width, height) = box.astype("int")
                # use the center (x, y)-coordinates to derive the top and
                # and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))
                # update our list of bounding box coordinates, confidences,
                # and class IDs
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # perform the non maximum suppression given the scores defined before
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, SCORE_THRESHOLD, IOU_THRESHOLD)

    if len(idxs) == 0:
        print("========== não detectou peixe ========= " + file_name)
        isFish = 0
    else:
        print("========== detectou peixe ========= " + file_name)
        isFish = 1
        if len(idxs) == 0:
            print("========== não detectou peixe ========= " + file_name)
            return image
        print(f"Boxes: {boxes}")
        print(f"Confidences: {confidences}")
        # perform the non maximum suppression given the scores defined before
        idxs = cv2.dnn.NMSBoxes(boxes, confidences, SCORE_THRESHOLD, IOU_THRESHOLD)

        boxes = [boxes[i] for i in idxs]

        boxes = sorted(boxes, key = lambda x : x[2]*x[3], reverse=True)
        confidences = [x for _,x in sorted(zip(boxes,confidences), key = lambda x : x[0][2]*x[0][3], reverse=True)]

        # Print debug information after sorting
        print(f"Boxes after sorting: {boxes}")
        print(f"Confidences after sorting: {confidences}")

        boxes = boxes[0]
        confidences = confidences[0]


        # extract the bounding box coordinates
        x, y = boxes[0], boxes[1]
        w, h = boxes[2], boxes[3]
        wp = round(w * 0.2)
        hp = round(h * 0.2)
        w = w + wp
        h = h + hp
        if w > h:
            diff = round((w - h)/2)
            h = w
            y = y - diff
        else:
            diff = round((h - w)/2)
            w = h
            x = x - diff
        # draw a bounding box rectangle and label on the image
        cv2.rectangle(image, (np.max([x,0]), np.max([y,0])), (x+w, y+h), color=color, thickness=thickness)
        text = f"Fish Detected {confidences:.2f}"
        print("========== detectou peixe ========= " + file_name)
        print(text)
        # calculate text width & height to draw the transparent boxes as background of the text
        (text_width, text_height) = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontScale=font_scale, thickness=thickness)[0]
        text_offset_x = x
        text_offset_y = y - 5
        box_coords = ((text_offset_x, text_offset_y), (text_offset_x + text_width + 2, text_offset_y - text_height))
        overlay = image.copy()
        cv2.rectangle(overlay, box_coords[0], box_coords[1], color=color, thickness=cv2.FILLED)
        # add opacity (transparency to the box)
        image = cv2.addWeighted(overlay, 0.6, image, 0.4, 0)
        # now put the text (label: confidence %)
        cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=font_scale, color=(0, 0, 0), thickness=thickness)
        #fi, ext = os.path.splitext(filename)
        #cv2.imwrite(out_path+fi+'_detected'+ext, image)
    return isFish
   