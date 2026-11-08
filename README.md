# Group 2 CV Project

IAT 360 group project. We draw mouse movements as images and train YOLO (yolo26n-cls) to tell if they came from a human or a bot.

## Setup

pip install ultralytics opencv-python pandas pyautogui pynput pillow websocket-client

## Scripts (in order)

1. human.py records human sessions on collector.html
2. robot.py records bot sessions (easy and hard are used, medium is not)
3. convert_json.py turns our recordings into CSV files
4. draw_mouse.py draws every CSV as an image into yolo_dataset
5. split_dataset.py splits the images 60/20/20 into yolo_split
6. train_model.py trains a model and saves the results in runs
7. test_model.py tests best_model.pt on the test images

You only need test_model.py to check our final model. The images are already made.

## Folders

- our_json_data: our recordings
- our_collected_data: our recordings as CSV files
- raw_csv_data: SapiMouse and DELBOT data
- yolo_dataset: all the images
- yolo_split: the train, val and test images
- runs: results from every training run and the final test
- best_model.pt: our final model (from runs/adamw_lr_0.0003_seed_1)
