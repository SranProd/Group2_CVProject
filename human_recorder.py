import csv
import time
from pynput import mouse, keyboard

PLOTS =["type", "t","x","y", "button", "pressed","dx","dy"] 
# PLOTS is where each movemevt is being recorded as type - is like what happened clic, move or install
# t - record seconds, x and y cursor positions , button - left or right, pressed - is true or not, dx and dy how much scrollig happened

occurence=[] # empty string for now 
start =None # for starting it is set to none

def now():
    return round(time.perf_counter()-start, 3) # https://docs.python.org/3/library/time.html#time.perf_counter

def on_click(x,y, button, pressed):
    occurence.append({"type":"click", "t":now(), "x":x, "y":y,"button":button.name, "pressed":pressed})
    # above code runs everytime the button is pressed or release , and button.name turns the click as text, and pressed record ture or false

def on_move(x,y):
    occurence.append ({"type":"move", "t":now(), "x":x, "y":y})
    # pynput calls this function every singe time mouse moves

def on_scroll(x,y,dx,dy):
    occurence.append({"type":"scroll", "t":now(),"x":x, "y":y,"dx":dx,"dy":dy})
    # pynput calls it whenever scrolling happens

def on_press(key):
    if key ==keyboard.Key.esc:
        return False

def main():
        global start
        print("Recording the mouse movements . Press Esc to STOP anytime")
        start=time.perf_counter()

        mouse_listen= mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        key_listen = keyboard.Listener(on_press=on_press)
        mouse_listen.start()
        key_listen.start()

        key_listen.join() # scripts waits until the keyboard movements stop
        mouse_listen.stop()

with open("human_movement.csv", "w", newline="") as f:

    writer=csv.DictWriter(f, fieldnames=PLOTS)
    writer.writeheader()
    writer.writerows(occurence)

    print(f"Saved {len(occurence)} occurence to the file human_movement.csv")

if __name__=="__main__":
    main()

