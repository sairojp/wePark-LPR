# wePark 
wePark is a project aimed to automate parking functionality in parking spot. It consists of LPR system which could detect the incoming vehicle and record their entry and exit time and update it in realtime. 
It consists of three applications : 
1. LPR system
2. Frontend app : https://github.com/sairojp/wePark-FE
3. Backend app  : https://github.com/sairojp/wePark-BE
This repository consists of LPR system which is responsible for :
1.Detect vehicles in real time using video input.
2.Detect License plate and perform ocr to read license plate number.
3.Record the entry time and license plate number and update it in mongodb database. 

It uses YOLO for object detection and EasyOCR. 

