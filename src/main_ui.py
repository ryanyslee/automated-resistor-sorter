# Source - https://stackoverflow.com/a/14819141
# Posted by Bryan Oakley, modified by community. See post 'Timeline' for change history
# Retrieved 2026-04-18, License - CC BY-SA 4.0

import tkinter as tk                # main GUI library
from tkinter import font
from theme import COLORS, FONT      # theme.py file: color palette, fonts
from event_list import get_event, Events, add_event # event list to communicate with main code

# library to keep previous configurations for bin --> resistor values
import json
import os
import math                         # keeps updated resistor values integers

# Base Page ---------------------------------------------------------------
# all class <name>(PAGE) will inherit these functions
class Page(tk.Frame):
    # initialize page; runs once on startup
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller    # to reference MainView
    
    # brings page to focus
    def show(self):
        self.lift()
        self.focus_set()   # interact with widgets only on the top window

# HOME PAGE ---------------------------------------------------------------
class home(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.config(bg=COLORS["bg"])
        self.bind("<Key>", self.on_key)     # link page to key presses / on_key function

        self.index = 0  # button selection index
        
        # UI ---------------------------------------
        # UI button parameters
        buttonWidth = 30
        buttonHeight = 3
        fontParam = (FONT["text"],25)
        
        # UI widgets
        centeringFrame = tk.Frame(self, bg=COLORS["bg"])
        centeringFrame.pack(expand=True)    # to align widgets in the center rather than an edge

        # create the children
        self.startButton = tk.Label(centeringFrame, text="Press to Start", font=fontParam, 
                                    width=buttonWidth, height=buttonHeight,
                                    relief="raised")
        self.configureButton = tk.Label(centeringFrame, text="Configure", font=fontParam,
                                         width=buttonWidth, height=buttonHeight,
                                         relief="raised")
        
        # display the children (.pack)
        self.startButton.pack(pady=10)
        self.configureButton.pack(pady=10)

        # keep track of buttons in the UI
        self.buttons = [self.startButton, self.configureButton]
        self.update_selection()     # to show the initial selection

    # update button and text color based on what is selected
    def update_selection(self):
        for i, btn in enumerate(self.buttons):
            if i == self.index:
                btn.config(bg=COLORS["selected"], fg=COLORS["selected_text"])
            else:
                btn.config(bg=COLORS["button"], fg=COLORS["button_text"])
    
    # respond to key presses
    def on_key(self, event):
        key = event.char

        if (key == "4") or (key == "7"):   # DOWN
            # prevented from wrapping down from the top
            if self.index < (len(self.buttons)-1):
                self.index = (self.index + 1) % len(self.buttons)
        elif (key == "1") or (key == "6"): # UP
            # prevented wrapping from the top to the bottom
            if self.index > 0:
                self.index = (self.index - 1) % len(self.buttons)  
        elif key == "8": # SELECT
            if self.index == 0:
                self.controller.p2.show()
                add_event(Events.PLAY_PRESS)
            elif self.index == 1:
                self.controller.p3.show()

        self.update_selection()     


# RUNNING PAGE ------------------------------------------------------------
class running(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.config(bg=COLORS["run_bg"])
        self.bind("<Key>", self.on_key)     # link page to key presses / on_key function

        # UI ----------------------------------
        # UI params
        fontParam = (FONT["text"], 20)
        buttonWidth = 30
        buttonHeight = 3

        # UI widgets
        centeringFrame = tk.Frame(self, bg=COLORS["run_bg"])   
        centeringFrame.pack(expand=True)

        # create the children
        self.runningLabel = tk.Label(centeringFrame, text="Status: Running", font=fontParam,
                                     bg=COLORS["run_bg"])
        #self.valueText = tk.StringVar(centeringFrame, "")
        #self.valueLabel = tk.Label(centeringFrame, textvariable=self.valueText, font=fontParam, bg=COLORS["run_bg"])
        self.valueDisplay = tk.Text(centeringFrame, font=fontParam, bg=COLORS["run_bg"], height=2, width=40, borderwidth=0, highlightthickness=0)
        self.valueDisplay.tag_configure("bold", font=(FONT["text"], 20, "bold"))
        self.valueDisplay.tag_configure("center", justify='center')
        self.returnHome_button = tk.Button(centeringFrame, text="Press 'Enter' to stop", font=fontParam, width=buttonWidth, height=buttonHeight)
        #self.valueDisplay.pack(pady=10)
        
        self.returnHome_button = tk.Button(centeringFrame, text="Press 'Enter' to stop",
                                           font=fontParam, width=buttonWidth, height=buttonHeight)
        
        # display the children
        self.runningLabel.pack(pady=(20, 5))
        self.valueDisplay.pack(pady = 10)
        self.returnHome_button.pack(pady=20)
        
        # Initialize text
        self.valueDisplay.insert("1.0", "")
        self.valueDisplay.config(state="disabled")

    def on_key(self, event):
        if event.char == "8":
            self.controller.p1.show()       # go to home page
            add_event(Events.PAUSE_PRESS)
            #self.valueText.set("")
            
            # Reset display text when stopping
            self.valueDisplay.config(state="normal")
            self.valueDisplay.delete("1.0", tk.END)
            self.valueDisplay.insert("1.0", "")
            self.valueDisplay.config(state="disabled")
        elif event.char == "t": # t for timeout
            self.controller.p5.show()
        # Add key to update resistor value (potentially update, delay 1s, delete)
        #elif event.char == "r": # r for read
        #    with open('cv_output.json', 'r') as file:
        #        data = json.load(file)
        #        self.valueText.set(f"{data['1']}, {data['2']}")
        
        elif event.char == "r": # r for read
            with open('cv_output.json', 'r') as file:
                data = json.load(file)
                resistor_val = data['1']  # e.g., "1M Ω"
                status_msg = data['2']    # e.g., "no bin assigned, moving to Reject Bin"

			# Unlock the widget to edit it
            self.valueDisplay.config(state="normal")
            self.valueDisplay.delete("1.0", tk.END)
			
			# Insert static prefix
            #self.valueDisplay.insert(tk.END, "Resistor Value: ")
			
			# Insert the actual value with the BOLD tag
            #.valueDisplay.insert(tk.END, resistor_val, "bold")
			
			# Insert the rest of the message normally
            #self.valueDisplay.insert(tk.END, f", {status_msg}")
			
			# Re-lock to prevent user typing in the UI
            #self.valueDisplay.config(state="disabled")
            
            # Re-insert the prefix we lost earlier
            #self.valueDisplay.insert(tk.END, "Resistor Value: ")
            self.valueDisplay.insert(tk.END, resistor_val, ("bold", "center"))
            self.valueDisplay.insert(tk.END, f", {status_msg}", "center")
            
            self.valueDisplay.config(state="disabled")

# HALTING PAGE ------------------------------------------------------------
class halt(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.config(bg=COLORS["halt_bg"])
        self.bind("<Key>", self.on_key)     # link page to key presses / on_key function

        # UI -------------------------------------
        # UI params
        fontParam = (FONT["text"], 20)
        buttonWidth = 30
        buttonHeight = 3

        # UI widgets
        centeringFrame = tk.Frame(self, bg=COLORS["halt_bg"])
        centeringFrame.pack(expand=True)

        # create the children
        self.runningLabel = tk.Label(centeringFrame, text="Status: <No resistor detected>", font=fontParam,
                                     bg=COLORS["bg"])
        self.returnHome_button = tk.Button(centeringFrame, text="Press 'Enter' to return home",
                                           font=fontParam, width=buttonWidth, height=buttonHeight)
        
        # display the children
        self.runningLabel.pack(pady=5)
        self.returnHome_button.pack(pady=20)
    
    def on_key(self, event):
        if event.char == "8":
            self.controller.p1.show()       # go to home page

# CONFIG PAGE ------------------------------------------------------------
class config(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.config(bg=COLORS["bg"])
        self.bind("<Key>", self.on_key)     # link page to key presses / on_key function

        # these variables will be defined below and in self.show()
        self.boxes = []
        self.value_labels = []
        self.reject_bin = 13 # reject bin is bin 13

        # UI -----------------------------------
        # UI params
        bin_btnWidth = 8		    
        bin_btnHeight = 3		
        fontParam = (FONT["text"],20)				# previously 18	
        fontParam_values = (FONT["numbers"], 17)	# previously 15
        
        # Return button
        self.return_btn = tk.Label(self, text="Return", font=(FONT["text"], 15),
                                   padx=25, pady=8, bg=COLORS["button"], relief="groove")
        self.return_btn.pack(anchor="nw", padx=5, pady=(8,0))  # (top padding, bot padding)
        
        # Center alignment frame (parent of binNum widgets)
        centeringFrame = tk.Frame(self, bg=COLORS["bg"])
        centeringFrame.pack(expand=True)

        # create 15 boxes (children) for each bin and display its corresponding resistor value
        for i in range(15):
            row = i // 5       # row (0–2)
            col = i % 5        # column (0–4)
			
            if (row == 2) and (col == 2):
                bg = "red"
                fg = COLORS["bg"]
            else:
                bg = COLORS["button"]
                fg = COLORS["button_text"]
			
            # define (smaller) parent frame (one for each bin button)
            frame = tk.Frame(centeringFrame, bg=bg, 
                             width=bin_btnWidth, height=bin_btnHeight,
                             relief="raised", borderwidth=2)
            frame.grid(row=row, column=col, padx=6, pady=(0,13))    # spacing between each bin button
            frame.grid_propagate(False) # stop button sizes from resizing bc of children widgets

            # define children of (smaller) frame to show bin # + resistor #
            binLabel = tk.Label(frame, bg=bg, fg=fg, text=f'Bin {str(i+1)}', font=fontParam,
                                width=bin_btnWidth)
            valueLabel = tk.Label(frame, bg=bg, fg=fg, text="--")

            # .pack(pady=(topPadding bottomPadding)) + display the children
            margins = 8
            binLabel.pack(pady=(margins, 0))
            valueLabel.pack(pady=(0, margins))    

            # for navigation: add frames "buttons" to the whole list  
            self.boxes.append(frame) # add the box to lists
            self.value_labels.append(valueLabel)

        self.buttons = [self.return_btn] + self.boxes   
        self.index = 1   # start on bin 1 button
        self.total = len(self.buttons)
        self.prev_index = self.index        # for faster display updates

        self.update_selection()
    
    # update highlighted button
    def update_selection(self):
        # only update old selected + new selected (reduce flickering)
        indices_to_update = [self.prev_index, self.index]

        for i in indices_to_update:
            if i < 0 or i >= len(self.buttons):
                continue    # ignores this index, checks the next index (the next button)
            
            # the index i has passed! it's format shall be changed, to what? you shall see ahead!!!
            btn = self.buttons[i]

            # RETURN BUTTON (index 0) ---
            if i == 0:
                if i == self.index:
                    bg = COLORS["selected"]
                    fg = COLORS["selected_text"]
                else:
                    bg = COLORS["button"]
                    fg = COLORS["button_text"]

                btn.config(bg=bg, fg=fg)
                continue
            
            # BIN NUMBER BUTTONS --------------
            if i == self.index:
                bg = COLORS["selected"]
                fg = COLORS["selected_text"]
            else:
                bg = COLORS["button"]
                fg = COLORS["button_text"]

            btn.config(bg=bg)

            # update colors in children of frame (buttons)
            for widget in btn.winfo_children():
                widget.config(bg=bg, fg=fg)

        # update tracker
        self.prev_index = self.index

    def on_key(self, event):
        key = event.char
        cols = 5

        directionMap = {"1":"up", "3":"left", "6": "left", "4":"down", "5":"right", "7": "right", "8":"Enter"}
        # RETURN BUTTON 
        if self.index == 0:
            if (key == "4") or (key == "5") or (key == "7"):  # DOWN or RIGHT arrow/dial → go to first row
                print(f"pressed {key}")
                self.index = 1
        # BIN SELECT GRID BUTTONS
        else:
            grid_index = self.index - 1  # convert to 0–14 bc return index was 0
            print(f"pressed {key} {directionMap[key]}")

            if (key == "3") or (key == "6"): # LEFT arrow or CCW dial	 
                next_index = self.index - 1
                if next_index == self.reject_bin:
                    next_index -= 1
                if next_index <= 15:
                    self.index = next_index

            elif key == "4": # DOWN
                if self.index == 8:
                    self.index = 12   
                elif grid_index + cols < 15:
                    next_index = self.index + cols
                    if next_index == self.reject_bin:
                        next_index -= 1   # go LEFT instead of skipping down
                    if next_index <= 15:
                        self.index = next_index

            elif (key == "5") or (key == "7"):   # RIGHT arrow or CW dial
                #if (grid_index % cols) < cols - 1:
                next_index = self.index + 1
                if next_index == self.reject_bin:
                    next_index += 1
                if next_index <= 15:
                    self.index = next_index

            elif key == "1": # UP
                if grid_index < cols:   # bins 1–5
                    self.index = 0      # go to Return button
                else:
                    next_index = self.index - cols

                    if next_index == self.reject_bin:
                        next_index -= cols

                    if next_index >= 1:
                        self.index = next_index

        # Pressing enter
        if key == "8":
            if self.index == 0:
                self.controller.p1.show()       # return home
                add_event(Events.UPDATE_VALUES)
            else:
                selected_bin = self.index       # store bin num of value being changed
                print("Selected bin:", selected_bin)

                self.controller.selected_bin = selected_bin     # make it globally accessible ("bin_num = self.controller.selected_bin")
                self.controller.p4.show()       # go pick a new resistor value for this bin :3

        self.update_selection()

    # defining more with show() because info can change each time it's called upon
    def show(self):
        super().show()  # keeps what the parent currently does

        # new feature for config.show(): every time config page is shown, update the resistor values being displayed
        for i in range(15):
            bin_num = i + 1

            if bin_num == 13:
                self.value_labels[i].config(text="REJECT")
            else:
                val = self.controller.assigned_values.get(bin_num)
                self.value_labels[i].config(text=self.controller.p4.format_resistor(val))


# BIN VALUE PAGE ------------------------------------------------------------
class binValueSelect(Page):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        self.bind("<Key>", self.on_key)     # again... links page to key presses / on_key function

        # E12 resistor series
        self.base_values = [1.0,1.2,1.5,1.8,2.0,2.2,2.7,3.3,3.9,4.7,5.6,6.8,8.2]
        self.multipliers = [1,10,100,1000,10000,100000,1000000]

        # Navigation indices
        self.nav_index = 0   # 0=base, 1=mult, 2=back
        self.base_index = 0
        self.mult_index = 0

        # UI --------------------------------------------
        # UI Params
        fontParam_value = (FONT["numbers"], 50) 
        fontParam_title = (FONT["text"], 35)
        fontParam_enter = (FONT["text"], 25)
        yHeight = 25    
        xWidth = 25
        btn_padx = 3
        btn_width = 8

        # page title 
        self.titleLabel = tk.Label(self, font=fontParam_title)        # update the text in self.show()
        self.titleLabel.pack(pady=(40, 0))

        # frame to center all 4 columns (le parent frame)
        mainFrame = tk.Frame(self)
        mainFrame.pack(expand=True)

        # create and place/display the childrennn (place with .grid to control location)
        # array of resistor base values (1.0 ohm, 1.2 ohm, etc.)
        self.baseLabel = tk.Label(mainFrame, padx=xWidth, pady=yHeight, relief="raised", font=fontParam_value)
        self.baseLabel.grid(row=0, column=0, padx=btn_padx)

        # multiple of 10 array labels
        self.multLabel = tk.Label(mainFrame, width=btn_width, pady=yHeight, relief="raised", font=fontParam_value)
        self.multLabel.grid(row=0, column=1, padx=btn_padx)

        # equals sign for clarity
        self.equals = tk.Label(mainFrame, text="=", pady=yHeight, font=fontParam_value)
        self.equals.grid(row=0, column=2, padx=(btn_padx, 0))   # (left, right padding)

        # the texts update after on_key (which calls update_display()) 
        self.previewLabel = tk.Label(mainFrame, font=fontParam_value, relief="flat",
                                     width=6, pady=yHeight)
        self.previewLabel.grid(row=0, column=3)

        # button to submit the resistor value :nodding
        self.enterLabel = tk.Label(self, text="Enter", padx=xWidth, font=fontParam_enter, relief="ridge")
        self.enterLabel.pack()
        
        # the texts update after on_key (which calls update_display()) 
        self.errorLabel = tk.Label(self, text="", fg="red", font=fontParam_enter)
        self.errorLabel.pack()

        self.update_display()

    # helper functions
    def format_resistor(self, value):
        #\u03A9 is ohm's Unicode
        if value >= 1_000_000: # mega ohm
            return f"{value/1_000_000:g} M\u03A9"
        elif value >= 1_000: # kilo ohm
            return f"{value/1_000:g} k\u03A9"  # in the hundreds
        else:
            return f"{value:g} \u03A9"

    def get_value(self):
        return self.base_values[self.base_index] * self.multipliers[self.mult_index]

    # display changes ---------------------
    def update_display(self):
        value = self.get_value()

        # update text in the UI! (ex. resistor values for base + multiplier + preview)
        self.baseLabel.config(text=str(self.base_values[self.base_index]))
        self.multLabel.config(text=f"x{self.multipliers[self.mult_index]}")
        self.previewLabel.config(text=self.format_resistor(value))

        # update selection color
        select = COLORS["selected"]
        selectText = COLORS["selected_text"]
        deselect = COLORS["button"]
        deselectText = COLORS["button_text"]

        self.baseLabel.config(bg=select if self.nav_index == 0 else deselect,
                              fg=selectText if self.nav_index == 0 else deselectText)
        self.multLabel.config(bg=select if self.nav_index == 1 else deselect,
                              fg=selectText if self.nav_index == 1 else deselectText)
        self.enterLabel.config(bg=select if self.nav_index == 2 else deselect,
                               fg=selectText if self.nav_index == 2 else deselectText)

    # keyPad input ----------
    def on_key(self, event):
        key = event.char
		
		# navigate between the 3 boxes (2 value boxes, 1 enter)
        if key == "3": # LEFT arrow/dial
            self.nav_index = (self.nav_index - 1) % 3
        elif (key == "5"):
            self.nav_index = (self.nav_index + 1) % 3	
        elif (key == "4"): 	# Down arrow (only works if on the top row for value changing boxes)
            if (self.nav_index == 0) or (self.nav_index == 1):
                self.nav_index = 2	# hard coding the enter button
        elif (key == "1"): 			# UP arrow;
            if self.nav_index == 2:	# when it's on the "enter" button
                self.nav_index = 0
        elif (key == "6"):			# CCW dial
            if self.nav_index == 0:
                self.base_index = (self.base_index - 1) % len(self.base_values)
            elif self.nav_index == 1:
                self.mult_index = (self.mult_index - 1) % len(self.multipliers)
        elif (key == "7"):
            if self.nav_index == 0:
                self.base_index = (self.base_index + 1) % len(self.base_values)
            elif self.nav_index == 1:
                self.mult_index = (self.mult_index + 1) % len(self.multipliers)
        elif key == "8": # ENTER
            if self.nav_index == 2:
                
                #block reject bin
                if self.controller.selected_bin == 13:
                    return

                value = self.get_value()

                # duplicate check
                for bin_num, val in self.controller.assigned_values.items():
                    if val == value and bin_num != self.controller.selected_bin:
                        self.errorLabel.config(text=f"Error: used in bin {bin_num}")
                        return

                # value deemed valid, now saving value
                if value > 10:
                    newVal = math.floor(value) #math.floor to keep the value as an integer
                else:
                    newVal = value
                self.controller.assigned_values[self.controller.selected_bin] = newVal  
                self.controller.save_values()

                # self.errorLabel.config(text="") # clear error text so it's not there next time page is called (moved to .show())
                self.controller.p3.show()       # go to config page
                return

        self.update_display()
        
    # for when this page is lifted to top ----------
    def show(self):
        super().show()

        # clear any potential previous changes/selections
        self.errorLabel.config(text="")
        bin_num = self.controller.selected_bin
        self.titleLabel.config(text=f"Select Value for Bin {bin_num}")
        self.nav_index = 0   # 0=base, 1=mult, 2=back;  # make sure the selection is on the base selection first

        # display the already assigned resistor value if it exists (different for each bin page)
        val = self.controller.assigned_values.get(bin_num)

        if val:
            found = False       # variable to determine when to stop looping through
            for i, base in enumerate(self.base_values):
                for j, mult in enumerate(self.multipliers):
                    if abs(base * mult - val) < 1e-6:   # the combination matches assigned value (1e-6 as approx 0)
                        # index found that matches the set resistor value
                        self.base_index = i
                        self.mult_index = j
                        found = True
                        break
                if found:
                    break
        else:   # if for some reason no resistor value was ever assigned
            self.base_index = 0
            self.mult_index = 0

        self.update_display()

# MAIN VIEW ------------------------------------------------------------
class MainView(tk.Frame):
    def __init__(self, root, filePath):
        super().__init__(root)
        self.filePath = filePath
        self.load_values()      # obtain the resistor values set for the bins

        self.selected_bin = 1   # just to have bin 1 selected as default when loaded

        # frame to contain all the pages
        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        # all the pages in this UI setup
        self.p1 = home(container, self)
        self.p2 = running(container, self)
        self.p3 = config(container, self)
        self.p4 = binValueSelect(container, self)
        self.p5 = halt(container, self)

        for page in (self.p1, self.p2, self.p3, self.p4, self.p5):
            page.place(x=0, y=0, relwidth=1, relheight=1)

        self.p1.show()

    # Managing bin to its resistor values -----------
    def save_values(self):
        with open(self.filePath, "w") as f:
            json.dump(self.assigned_values, f)

    def load_values(self):
        if os.path.exists(self.filePath):
            try:
                with open(self.filePath, "r") as f:
                    data = json.load(f)

                self.assigned_values = {int(k): v for k, v in data.items()}

            # if the json file doesn't work for some reason...
            except (json.JSONDecodeError, ValueError):
                print("Corrupted JSON file — loading defaults.")
                self.load_defaults()    # use the pre-determined default values
        else:
            self.load_defaults()
    
    # use in case (1) json file doesn't exist, (2) json file isn't working
    def load_defaults(self):
        # default values 
        self.assigned_values = {
            1: 100,
            2: 220,
            3: 330,
            4: 470,
            5: 1000,
            6: 2200,
            7: 3300,
            8: 4700,
            9: 10000,
            10: 22000,
            11: 33000,
            12: 47000,
            13: 0,
            14: 220000,
            15: 1000000
        }

def shut_down():
	global root
	root.destroy()
	root = None
	import gc
	gc.collect()
	add_event(Events.DONE)


def run_ui():
	global root
	root = tk.Tk()
	root.geometry("800x480")    # HDMI resolution
	root.attributes('-fullscreen', True)
	root.config(cursor="none") # Disables cursor
	root.bind("x", lambda event: shut_down()) 
	app = MainView(root, "resistor_values.json")
	app.pack(fill="both", expand=True)
	root.mainloop()

if __name__ == "__main__":
    run_ui()
