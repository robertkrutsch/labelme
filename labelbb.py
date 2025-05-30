import cv2
import numpy as np
from zod import ZodFrames, ZodSequences
from zod.anno.object import OBJECT_CLASSES, ObjectAnnotation
from zod.cli.utils import Version
from zod.constants import AnnotationProject, Anonymization
from zod.data_classes.frame import ZodFrame
from zod.utils.utils import str_from_datetime
import math

from tkinter import Label,Tk, Button,ttk,ALL
import tkinter as tk

from PIL import Image,ImageTk
import random
from tkinter import filedialog as fd
import os
from fnmatch import fnmatch
import csv
from bb import BBox


Color_Scheme = {
'Car':'red', 
'Van':'chartreuse', 
'Truck':'pink', 
'Bus':'orange',
'Cyclist':'green', 
'Motorcycle':'tan', 
'Pedestrian':'yellow' 
}

class ImageList():
    '''
            LIST OF FILE NAMES TO ANNOTATE
    '''
    def __init__(self):
        self.image_list = [] #img names
        self.anno_list = [] #anno file names
        self.annos = [] #all annotations from files
        self.idx = 0
        self.length_list = 0 #number of images
        self.anno_list_length = 0 # number of annotation files

    def reset(self):
        self.image_list = []
        self.anno_list = []
        self.annos = []
        self.idx = 0
        self.length_list = 0
        self.anno_list_length = 0

    def _read_anno_file(self,fn):
        anno_list = []
        with open(fn, newline='') as f:
            reader = csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONE)
            for row in reader:
                row[1:] = [int(float(str)) for str in row[1:]]
                anno_list.append(row)
        return anno_list

    def populate_im_list(self,dir_name):
        for path, subdirs, files in os.walk(dir_name):
            for name in files:
                if fnmatch(name, "*.jpg"):
                    self.image_list.append(os.path.join(path, name))
        self.length_list = self.image_list.__len__()
    
    def populate_anno_list(self,dir_name):
        for path, subdirs, files in os.walk(dir_name):
            for name in files:
                if fnmatch(name, "*.txt"):
                    self.anno_list.append(os.path.join(path, name))
                    self.annos.append(self._read_anno_file(os.path.join(path, name)))
        self.anno_list_length = self.anno_list.__len__()

    def get_file_name(self):
        return self.image_list[self.idx]
    
    def inc_idx(self):
        self.idx +=1
        if self.length_list==self.idx:
            self.idx = 0
    
    def is_empty(self):
        return self.length_list==0
    def dec_idx(self):
        self.idx -=1
        if self.idx==-1:
            self.idx = self.length_list-1

class AutoScrollbar(ttk.Scrollbar):
    ''' A scrollbar that hides itself if it's not needed.
        Works only if you use the grid geometry manager '''
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
            ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kw):
        raise tk.TclError('Cannot use pack with this widget')

    def place(self, **kw):
        raise tk.TclError('Cannot use place with this widget')

class Toolbar(ttk.Frame):

    def __init__(self,root):
        self.root = root
        self.root.title("LabelMe")
        self.root.bind('<KeyPress>', self.shortcuts)

        self._create_layout() #create layout first , canvas and side frame
        self._create_obj_frame(position=0) #create the annotation gui
        self._creat_load_save_frame(position=1) # create the load save gui
        self._create_status_frame(position=3) #print the x,y position in the image coordinates
        self._create_shortcuts_frame(position=4)
        self._rest_params()

        self.image_list = ImageList()

    def _find_nearest_point(self,x,y):
            d_min = 100000000
            idx_min = -1
            obj_min = -1
            for obj in range(self.anno_list.__len__()):
                for idx in range(int((self.anno_list[obj].__len__()+1)/2)):
                    d = (self.anno_list[obj][2*idx] - x)**2 + (self.anno_list[obj][2*idx+1] - y)**2
                    if d_min > d:
                        d_min = d
                        idx_min = idx
                        obj_min = obj

            return obj_min,idx_min
    def _create_obj_frame(self,position=2):
        self.obj_frame = tk.Frame(self.toolbar_frame,borderwidth=2,relief=tk.RIDGE)
        self.obj_frame.grid(row=position,column=0,padx=2,pady=2)

        self.op_selection_box = ttk.Combobox(self.obj_frame,width=15)
        self.op_selection_box['values'] = ('Select','2D-BB','Delete')
        self.op_selection_box.current(0)
        self.op_selection_box.bind('<<ComboboxSelected>>', self.op_selection_box_modified)   
        self.op_selection_box.grid(row=0,column=0,padx=5,pady=5) 

        self.obj_selection_box = ttk.Combobox(self.obj_frame,width=15)
        self.obj_selection_box['values'] = ('Car','Van','Truck','Bus','Cyclist','Motorcycle','Pedestrian')
        self.obj_selection_box.current(0)
        self.obj_selection_box.grid(row=1,column=0,padx=5,pady=5) 


        self.zoomin_button = ttk.Button(self.obj_frame,text="Add",command=self.addobject,width=15)
        self.zoomin_button.grid(row=2,column=0,padx=5,pady=5)

        self.saveobj_button = ttk.Button(self.obj_frame,text="Save",command=self.saveobj,width=15)
        self.saveobj_button.grid(row=3,column=0,padx=5,pady=5)
    def _create_layout(self):
        self.toolbar_frame = ttk.Frame(self.root)
        self.toolbar_frame.pack(side='left',fill = tk.Y)

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fil=tk.BOTH,expand=True)


        vbar = AutoScrollbar(self.main_frame, orient='vertical')
        hbar = AutoScrollbar(self.main_frame, orient='horizontal')
        vbar.grid(row=0, column=1, sticky='ns')
        hbar.grid(row=1, column=0, sticky='we')
        self.canvas = tk.Canvas(self.main_frame, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.grid(row=0, column=0, sticky='nswe')
        self.canvas.update()  # wait till canvas is created
        vbar.configure(command=self.scroll_y)  # bind scrollbars to the canvas
        hbar.configure(command=self.scroll_x)
        # Make the canvas expandable
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        # Bind events to the Canvas
        self.canvas.bind('<Configure>', self.show_image)  # canvas is resized
        self.canvas.bind('<ButtonPress-1>', self.mouseb1_press)
        self.canvas.bind('<B1-Motion>',     self.mouseb1_hold)
        self.canvas.bind('<B1-ButtonRelease>', self.mouseb1_release)
        self.canvas.bind('<ButtonPress-2>', self.move_from)
        self.canvas.bind('<B2-Motion>',     self.move_to)
        self.canvas.bind('<MouseWheel>', self.wheel)  # with Windows and MacOS, but not Linux
        self.canvas.bind('<Button-5>',   self.wheel)  # only with Linux, wheel scroll down
        self.canvas.bind('<Button-4>',   self.wheel)  # only with Linux, wheel scroll up 
        self.canvas.bind('<Motion>', self.mousemove)
        self.container = self.canvas.create_rectangle(0, 0, 0, 0, width=0)
    def _creat_load_save_frame(self,position):
        self.loadsave_frame = tk.Frame(self.toolbar_frame,borderwidth=2,relief=tk.RIDGE)
        self.loadsave_frame.grid(row=position,column=0,padx=2,pady=2)

        self.loadimage_button = ttk.Button(self.loadsave_frame,text="Load Image", width=15,command=self.load_button_command)
        self.loadimage_button.grid(row=0,column=0,padx=5,pady=5)
        self.loadimagewithanno_button = ttk.Button(self.loadsave_frame, width=15,text="Load Image & Anno",command=self.loadanno_button_command)
        self.loadimagewithanno_button.grid(row=1,column=0,padx=5,pady=5)
    def _create_status_frame(self,position):
        self.status_frame = tk.Frame(self.toolbar_frame,borderwidth=2,relief=tk.RIDGE)
        self.status_frame.grid(row=position,column=0,padx=2,pady=2)
        
        self.x_label = Label(self.status_frame, text="X: ")  
        self.x_label.grid(row=0,column=0,padx=5,pady=5)    
        
        self.y_label = Label(self.status_frame, text="Y: ")      
        self.y_label.grid(row=1,column=0,padx=5,pady=5)       
    def _create_shortcuts_frame(self,position):
        self.shortcuts_frame = tk.Frame(self.toolbar_frame,borderwidth=2,relief=tk.RIDGE)
        self.shortcuts_frame.grid(row=position,column=0,padx=2,pady=2)
        self.shortcuts_label = Label(self.shortcuts_frame, text=" s: Select \n a: Save \n c : Car(red) \n v : Van(chartreuse) \n t: Truck(pink) \n b : Bus(orange) \n y : Cyclist(green) \n m : Motocycle(tan) \n p : Pedestrian (yellow) ",justify="left")  
        self.shortcuts_label.grid(row=0,column=0,padx=5,pady=5)    
    def _load_image_to_canvas(self):
        self.image = Image.open(self.image_list.get_file_name())  # open image
        self.root.title(os.path.split(self.image_list.get_file_name())[1])
        self.width, self.height = self.image.size
        self.canvas.delete('all')
        self.container = self.canvas.create_rectangle(0, 0, self.width, self.height, width=0)
        self.show_image()
    def _rest_params(self):
        self.state_drawing = "None"
        self.side2d = [] # Sides 
        self.bboxes = []
        self.nr_bboxes = 0
        self.anno_list=[]
        self.anno_obj_type = [] #coresponds to the anno_list 
        self.anno_bb_tyepe = [] # bb list
        self.nr_2dsides = 0
        self.obj_selected = -1
        self.start_drawing = 0 # once we click the butten we can start drawing and we create an object
        self.imscale = 1.0  # scale for the canvaas image
        self.delta = 1.3  # zoom magnitude
        
    def _write_anno_file(self):

        if self.anno_list.__len__() > 0:
            with open(self.image_list.get_file_name() + ".txt", mode='w') as f: #only write if the list is not empty
                employee_writer = csv.writer(f, delimiter=',')
                for i in range(self.anno_list.__len__()):
                    employee_writer.writerow([self.anno_obj_type[i], self.anno_list[i][0],self.anno_list[i][1],self.anno_list[i][2],self.anno_list[i][3]])


    '''
        Buttons and keypresses
    '''

    def addobject(self):

        if self.state_drawing=="2D-BB":
            #BBox(self.canvas,width=2,color=Color_Scheme[b[0]],corners=[b[1], b[2],b[3],b[4]],state_box=1)
            self.bboxes.append(BBox(self.canvas,width = 2,color=Color_Scheme[self.obj_selection_box.get()],corners=[],state_box=0))
            self.nr_bboxes+=1


    def op_selection_box_modified(self,event):
        if self.op_selection_box.get()=='Delete':
            if self.nr_bboxes > 1:
                self.state_drawing = self.op_selection_box.get()
        else:
            self.state_drawing = self.op_selection_box.get()

    def saveobj(self):
        self._write_anno_file()
        self.state_drawing = "None"

    def shortcuts(self,event):
        if not self.image_list.is_empty():
            if event.keysym=='Right':
                self.saveobj()
                self.image_list.inc_idx()
                self._rest_params()
                self._load_image_to_canvas()
                self.show_anno()

            elif event.keysym=='Left':
                self.saveobj()
                self.image_list.dec_idx()
                self._rest_params()
                self._load_image_to_canvas()
                self.show_anno()

            elif event.keysym in ['c','v','t','b','y','m','p']:             
                self.op_selection_box.current(1) 
                self.obj_selection_box.current(['c','v','t','b','y','m','p'].index(event.keysym))
                self.state_drawing = "2D-BB"
                self.addobject()
            
            if event.keysym=='a': # Save
                self.saveobj()

            if event.keysym=='s':
                self.op_selection_box.current(0) #switch to selct
                self.state_drawing="Select"

            if event.keysym=='BackSpace' and self.nr_bboxes > 1:
                self.op_selection_box.current(2) 
                self.state_drawing="Delete"



    def load_button_command(self):
        dir_name = fd.askdirectory(initialdir="/Users/robertkrutsch/Documents/Code/VD/data/mini")
        self.image_list.populate_im_list(dir_name)
        self._load_image_to_canvas()

    def loadanno_button_command(self):
        self.image_list.reset()
        self._rest_params()
        dir_name = fd.askdirectory(initialdir="/Users/robertkrutsch/Documents/Code/VD/data/mini")
        self.image_list.populate_im_list(dir_name)
        self.image_list.populate_anno_list(dir_name)
        self._load_image_to_canvas()
        self.show_anno()
        self.state_drawing="Select"
    

    '''
    MOUSE EVENTS
    '''

    def mousemove(self, event):
        if not self.image_list.is_empty(): # show only if we have some images loaded
            x = self.canvas.canvasx(event.x) 
            y = self.canvas.canvasy(event.y)
            bbox = self.canvas.coords(self.container)
            self.x_label.config(text = " X: " + str(int( (x - bbox[0])/self.imscale )))
            self.y_label.config(text = " Y: " + str(int( (y - bbox[1])/self.imscale))) 

    def mouseb1_press(self,event):
        x = self.canvas.canvasx(event.x) 
        y = self.canvas.canvasy(event.y)

        if self.state_drawing=="2D-BB":
            bbox = self.canvas.coords(self.container)
            self.bboxes[self.nr_bboxes-1].start_box(x,y,bbox[0],bbox[1],self.imscale)
            #self.bboxes[self.nr_bboxes-1].selct_side(x,y,bbox[0],bbox[1],self.imscale)
        elif self.state_drawing=="Select":
            bbox = self.canvas.coords(self.container)

            obj_min,idx_min = self._find_nearest_point((x - bbox[0])/self.imscale, (y - bbox[1])/self.imscale )
            self.bboxes[obj_min].selct_side(x,y,bbox[0],bbox[1],self.imscale)
            self.obj_selected = obj_min
        elif self.state_drawing=="Delete" and self.nr_bboxes > 1:
            bbox = self.canvas.coords(self.container)
            obj_min,idx_min = self._find_nearest_point((x - bbox[0])/self.imscale, (y - bbox[1])/self.imscale )
            
            self.bboxes[obj_min].reset()
            self.bboxes.pop(obj_min)
            self.anno_obj_type.pop(obj_min)
            self.anno_list.pop(obj_min)
            self.nr_bboxes-=1
            #self.state_drawing="Select"

    def mouseb1_hold(self,event):
        x = self.canvas.canvasx(event.x) 
        y = self.canvas.canvasy(event.y)

        if self.state_drawing=="2D-BB":
            bbox = self.canvas.coords(self.container)
            self.bboxes[self.nr_bboxes-1].draw_box(x,y,bbox[0],bbox[1],self.imscale)
            #self.bboxes[self.nr_bboxes-1].move_side(x,y,bbox[0],bbox[1],self.imscale)
        elif self.state_drawing=="Select":
            bbox = self.canvas.coords(self.container)
            self.bboxes[self.obj_selected].move_side(x,y,bbox[0],bbox[1],self.imscale)

    def mouseb1_release(self,event):
        x = self.canvas.canvasx(event.x) 
        y = self.canvas.canvasy(event.y)

        if self.state_drawing=="2D-BB":
            bbox = self.canvas.coords(self.container)
        

            corners = self.bboxes[self.nr_bboxes-1].stop_box(x,y,bbox[0],bbox[1],self.imscale)
            if corners.__len__()!=0 : 
                self.anno_list.append(corners)
                self.op_selection_box.current(0) #switch to selct
                self.anno_obj_type.append(self.obj_selection_box.get())
                self.state_drawing="Select"


        elif self.state_drawing=="Select": 
            bbox = self.canvas.coords(self.container)
            corners = self.bboxes[self.obj_selected].stop_side(x,y,bbox[0],bbox[1],self.imscale) 
            if corners.__len__()!=0 : 
                self.anno_list[self.obj_selected] = corners

    def wheel(self, event):
        ''' Zoom with mouse wheel '''
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        bbox = self.canvas.bbox(self.container)  # get image area
        if bbox[0] < x < bbox[2] and bbox[1] < y < bbox[3]: pass  # Ok! Inside the image
        else: return  # zoom only inside image area
        scale = 1.0
        # Respond to Linux (event.num) or Windows (event.delta) wheel event
        if event.delta < 0:  # scroll down
            i = min(self.width, self.height)
            if int(i * self.imscale) < 30: return  # image is less than 30 pixels
            self.imscale /= self.delta
            scale        /= self.delta
        if event.delta > 0:  # scroll up
            i = min(self.canvas.winfo_width(), self.canvas.winfo_height())
            if i < self.imscale: return  # 1 pixel is bigger than the visible area
            self.imscale *= self.delta
            scale        *= self.delta
        self.canvas.scale('all', x, y, scale, scale)  # rescale all canvas objects
        #after scaling the size will be x * scale - x, y*scale-y , origx * scale - x*scale + x,origy * scale - y*scale + y
        # it will scale out from the point the mouse is
        self.show_image()

    def move_from(self, event):
        ''' Remember previous coordinates for scrolling with the mouse '''
        self.canvas.scan_mark(event.x, event.y)

    def move_to(self, event):
        ''' Drag (move) canvas to the new position '''
        self.canvas.scan_dragto(event.x, event.y, gain=1)
        self.show_image()  # redraw the image
    
    def scroll_y(self, *args, **kwargs):
        ''' Scroll canvas vertically and redraw the image '''
        self.canvas.yview(*args, **kwargs)  # scroll vertically
        self.show_image()  # redraw the image

    def scroll_x(self, *args, **kwargs):
        ''' Scroll canvas horizontally and redraw the image '''
        self.canvas.xview(*args, **kwargs)  # scroll horizontally
        self.show_image()  # redraw the image

    '''
        show images and show annotation an building the annotation lists
    '''

    def show_anno(self):
        for i in range(self.image_list.annos.__len__()):
            if self.image_list.anno_list[i][:-4]==self.image_list.get_file_name():
                for b in self.image_list.annos[i]:
                   
                    #create a box and add it 
                    box = BBox(self.canvas,width=2,color=Color_Scheme[b[0]],corners=[b[1], b[2],b[3],b[4]],state_box=1)
                    box.rect = self.canvas.create_rectangle(b[1], b[2],b[3],b[4],width=2,outline=Color_Scheme[b[0]])
                    box.corners = [b[1], b[2],b[3],b[4]]
                    box.state_box = 1
                    self.bboxes.append(box)
                    self.nr_bboxes+=1

                    self.anno_list.append([b[1], b[2],b[3],b[4]])
                    self.anno_obj_type.append(b[0])
        
    def show_image(self, event=None):
        ''' Show image on the Canvas '''
        bbox1 = self.canvas.bbox(self.container)  # get image area
        # Remove 1 pixel shift at the sides of the bbox1
        bbox1 = (bbox1[0] + 1, bbox1[1] + 1, bbox1[2] - 1, bbox1[3] - 1)
        bbox2 = (self.canvas.canvasx(0),  # get visible area of the canvas
                 self.canvas.canvasy(0),
                 self.canvas.canvasx(self.canvas.winfo_width()),
                 self.canvas.canvasy(self.canvas.winfo_height()))
        bbox = [min(bbox1[0], bbox2[0]), min(bbox1[1], bbox2[1]),  # get scroll region box
                max(bbox1[2], bbox2[2]), max(bbox1[3], bbox2[3])]
        if bbox[0] == bbox2[0] and bbox[2] == bbox2[2]:  # whole image in the visible area
            bbox[0] = bbox1[0]
            bbox[2] = bbox1[2]
        if bbox[1] == bbox2[1] and bbox[3] == bbox2[3]:  # whole image in the visible area
            bbox[1] = bbox1[1]
            bbox[3] = bbox1[3]
        self.canvas.configure(scrollregion=bbox)  # set scroll region
        x1 = max(bbox2[0] - bbox1[0], 0)  # get coordinates (x1,y1,x2,y2) of the image tile
        y1 = max(bbox2[1] - bbox1[1], 0)
        x2 = min(bbox2[2], bbox1[2]) - bbox1[0]
        y2 = min(bbox2[3], bbox1[3]) - bbox1[1]
        if int(x2 - x1) > 0 and int(y2 - y1) > 0:  # show image if it in the visible area
            x = min(int(x2 / self.imscale), self.width)   # sometimes it is larger on 1 pixel...
            y = min(int(y2 / self.imscale), self.height)  # ...and sometimes not
            image = self.image.crop((int(x1 / self.imscale), int(y1 / self.imscale), x, y))
            imagetk = ImageTk.PhotoImage(image.resize((int(x2 - x1), int(y2 - y1))))
            imageid = self.canvas.create_image(max(bbox2[0], bbox1[0]), max(bbox2[1], bbox1[1]),
                                               anchor='nw', image=imagetk)
            self.canvas.lower(imageid)  # set image into background
            self.canvas.imagetk = imagetk  # keep an extra reference to prevent garbage-collection


if __name__ == "__main__":

    win = Tk()
    win.state('zoomed')

    t = Toolbar(win)
    win.mainloop()

#TODO - something in selection does not work