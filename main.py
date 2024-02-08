from ultralytics import YOLO
import cv2
from deep_sort_realtime.deepsort_tracker import DeepSort
from util import *
import easyocr
import pymongo 
import os
from dotenv import load_dotenv

load_dotenv()
Connection = os.getenv('CONNECTION')


plate_nump_back_temp = ''
score_temp = 0
plate_nump_temp = ''




client = pymongo.MongoClient(Connection)

database = client["Yolo"]

collection = database["vehicles"]

# Initialize the OCR reader
reader = easyocr.Reader(['en'], gpu=True)

final_results = {}
update = {}
# imports are always needed
import torch


# # get index of currently selected device
# print(torch.cuda.current_device()) 


# # get number of GPUs available
# print(torch.cuda.device_count()) 


# # get the name of the device
# print(torch.cuda.get_device_name(0)) 

mot_tracker = DeepSort(max_age = 5,
                       n_init=2,
                       nms_max_overlap=1.0,
                       max_cosine_distance=0.3,
                       nn_budget=None,
                       override_track_class=None,
                       embedder="mobilenet",
                       half=True,
                       bgr=True,
                       embedder_gpu=True,
                       embedder_model_name=None,
                       embedder_wts=None,
                       polygon=False,
                       today=None)

frame_num = -1
#loading YOLO model 
vehicle_model = YOLO('yolov8n.pt')
plate_detector = YOLO('best.pt')
vehicles = [2]
#assigning video path and reading video 
video_path="Number Plate - Google Drive_2.mp4" 
cap = cv2.VideoCapture(video_path)
platedata = []
#reading frames 
success = True 
while success:
  success, frame = cap.read()
  frame_num += 1
  results_ = []
  data = []
  
  if success :
    final_results[frame_num] = {}
    print(frame_num)

    detections = vehicle_model(frame)[0]
    detections_=[]
    for detection in detections.boxes.data.cpu().numpy().tolist(): 
      
      x1,y1,x2,y2,score , class_id = detection
      w = x2 - x1
      h = y2 - y1
      if int(class_id) in vehicles:
        list1 = [x1,y1,w,h]
        mytuple = (list1,score,'car')
        detections_.append(mytuple)
        
    

    tracking_ids = mot_tracker.update_tracks(detections_,frame=frame)


    # for tracking_id in tracking_ids:
    #   if not tracking_id.is_confirmed():
    #     continue
    #   track_id = tracking_id.track_id
    #   ltrb = tracking_id.to_ltrb()
    #   bbox = ltrb 
    #   print('trackid')
    #   print(track_id)
    #   print(ltrb)

      # cv2.rectangle(frame,(int(bbox[0]), int(bbox[1])),(int(bbox[2]), int(bbox[3])),(0,0,255),2)
      # cv2.putText(frame, "ID: " + str(track_id), (int(bbox[0]), int(bbox[1] - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)






    results = plate_detector(frame)[0]
    

    for result in results.boxes.data.cpu().numpy().tolist(): 
      x1,y1,x2,y2,score,class_id = result
      xcar1, ycar1, xcar2, ycar2, car_id ,car_time = get_car(result, tracking_ids)
      # results_.append([xcar1, ycar1, xcar2, ycar2 ,car_id])
      # print (results_)
      # results_.append([x1, y1, x2, y2, score ,class_id])




      license_plate_crop = frame[int(y1):int(y2),int(x1) : int(x2)]
      up_width =  int ((x2-x1) * 2)
      up_height = int ((y2 -y1) *2)
      up_points = (up_width, up_height)
      license_plate_upscale =  cv2.resize(license_plate_crop, up_points, interpolation= cv2.INTER_LINEAR)

      license_plate_corp_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
      _ , license_plate_crop_thresh = cv2.threshold(license_plate_corp_gray, 64, 255, cv2.THRESH_BINARY_INV)

      plate , score ,type = read_license_plate(license_plate_crop_thresh)

      if plate is not None:
        final_results[frame_num][car_id] = {'car':{'bbox': [xcar1, ycar1, xcar2, ycar2] },'license_plate': {'bbox':[x1,y1,x2,y2],'text':plate,
        'bbox_score':score,'text_score':score}}

        # update = {
        #   'frame_nmr': int(frame_num),
        #   'car_id':int(car_id),
        #   'car_bbox':"[" + str(xcar1) + str(ycar1) + str(xcar2) + str(ycar2)+ "]",
        #   'license_plate_bbox': "[" + str(x1) + str(y1) + str(x2) + str(y2) + "]",
        #   'license_number':plate,
        #   'license_number_score':int(score)
        # }
        if type == 'front':
          update = {
          'frame_nmr': int(frame_num),
          'car_id':int(car_id),
          'car_bbox':"[" + str(xcar1) + " "+ str(ycar1) + " " + str(xcar2) + " " + str(ycar2)+ "]",
          'license_plate_bbox': "[" + str(x1) + " "+ str(y1) + " "+ str(x2) + " "+ str(y2) + " "+ "]",
          'license_number':plate,
          'license_number_score':float(score),
          'entry_time': car_time,
          'exit_time': '',
          'exited': bool(False)
          }
          if (update_DB_front(plate ,score,score_temp,plate_nump_temp)):
            collection.insert_one(update)
            score_temp = score 
            plate_nump_temp = plate

        elif type == 'back':
          if (update_DB_back(plate ,plate_nump_back_temp)):
            query = {"$set": {"exit_time":car_time,"exited":bool(True)}}
            collection.update_one({"license_number" :plate},query)
            plate_nump_back_temp = plate

      
      # if plate is not None:
      #   results_.append([x1, y1, x2, y2, score ,car_id ,plate,score])
      
      # print(results_)
      # cv2.imshow('img',license_plate_crop)
      # cv2.imshow('img2',license_plate_crop_thresh)
      # cv2.waitKey(0)

      # plate = reader.readtext(license_plate_crop_thresh) 


      
      # for(bbox,text,prob) in plate:
      #   if(prob > 0.5):
      #     print('this is text')
      #     print(text)
      #     print(prob)
      #     platedata.append([text , prob])

print(final_results)
# write_csv(final_results, './test.csv')
cap.release()
cv2.destroyAllWindows()    



