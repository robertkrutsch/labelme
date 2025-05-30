from tkinter import Label,Tk, Button,ttk,ALL
import tkinter as tk
from PIL import Image,ImageTk
import random
from tkinter import filedialog as fd
import os
from fnmatch import fnmatch
import csv
import numpy as np

class BBox:

    #Convert coordinates
    def _convert_to_image_coodinates(self,x,y,x_offset,y_offset,scale):
            return (x - x_offset)/scale, (y - y_offset)/scale  
    def _convert_to_canvas_coodinates(self,x,y,x_offset,y_offset,scale):
            return (x *scale + x_offset), (y * scale + y_offset)

    #Init and reset
    def __init__(self,canvas, width=2,color='red',corners=[],state_box=0):
        #corners and start are all in image coordinates we move back and forward to make sure we are consistent when we draw
        #user can then zoom and pan without issues of coordinate changes
        self.canvas = canvas
        self.width = width
        self.corners = corners 

        self.start_x = -1
        self.start_y = -1

        self.rect = None
        self.edge_change = None
        
        self.state_box = state_box
        self.color = color#color scheme

    def reset(self):
        self.canvas.delete(self.rect)
        self.corners = []
        self.scale_drawing = []
        self.start_x = -1
        self.start_y = -1
        self.rect = None
        self.state_box = 0
        self.idx = -1
        

    #DRAWING A 2D SIDE

    def start_box(self,x,y,x_offset,y_offset,scale):
        
        if self.state_box ==0:
            x_in_im, y_in_im = self._convert_to_image_coodinates(x,y,x_offset,y_offset,scale)
            self.start_x = x_in_im
            self.start_y = y_in_im
            self.corners.append(x_in_im)
            self.corners.append(y_in_im)
       
    def draw_box(self,x,y,x_offset,y_offset,scale):
        if self.state_box ==0:
            x_in_canvas, y_in_canvas = self._convert_to_canvas_coodinates(self.start_x,self.start_y,x_offset,y_offset,scale)
            self.canvas.delete(self.rect)
            self.rect = self.canvas.create_rectangle(x_in_canvas, y_in_canvas,x,y,width=2,outline=self.color)

    def stop_box(self,x,y,x_offset,y_offset,scale):
          if self.state_box ==0:
               x_in_im, y_in_im = self._convert_to_image_coodinates(x,y,x_offset,y_offset,scale)
               self.corners.append(x_in_im)
               self.corners.append(y_in_im)
        
               x_in_canvas, y_in_canvas = self._convert_to_canvas_coodinates(self.start_x,self.start_y,x_offset,y_offset,scale)
               self.canvas.delete(self.rect)
               self.rect = self.canvas.create_rectangle(x_in_canvas, y_in_canvas,x,y,width=2,outline=self.color)
               self.state_box = 1 #done drawing this now we can do fine tunning of the box
               return self.corners
          else:
               return []

    '''
        (x0,y0)  A..........................B



                D..........................C (x1,y1)


    '''
    def selct_side(self,x,y,x_offset,y_offset,scale):
         if self.state_box ==1:
            x_in_im, y_in_im = self._convert_to_image_coodinates(x,y,x_offset,y_offset,scale)
            l = np.zeros(4)
            l[0] = self.corners[0] - x_in_im
            l[1] = self.corners[1] - y_in_im
            l[2] = self.corners[2] - x_in_im
            l[3] = self.corners[3] - y_in_im
            self.idx = np.argmin(np.abs(l))

            x0_in_canvas, y0_in_canvas = self._convert_to_canvas_coodinates(self.corners[0],self.corners[1],x_offset,y_offset,scale)
            x1_in_canvas, y1_in_canvas = self._convert_to_canvas_coodinates(self.corners[2],self.corners[3],x_offset,y_offset,scale)
            self.canvas.delete(self.rect)
            if self.idx == 0 : #AD
                 self.rect = self.canvas.create_rectangle(x0_in_canvas, y0_in_canvas,x1_in_canvas, y1_in_canvas,width=2,outline=self.color)
                 #self.edge_change = self.canvas.create_line(x0_in_canvas, y0_in_canvas, x0_in_canvas, y1_in_canvas, fill='yellow', width=2)
            if self.idx == 1 : #AB
                 self.rect = self.canvas.create_rectangle(x0_in_canvas, y0_in_canvas,x1_in_canvas, y1_in_canvas,width=2,outline=self.color)
                 #self.edge_change = self.canvas.create_line(x0_in_canvas, y0_in_canvas, x1_in_canvas, y0_in_canvas, fill='yellow', width=2)
            if self.idx == 2 : #BC
                 self.rect = self.canvas.create_rectangle(x0_in_canvas, y0_in_canvas,x1_in_canvas, y1_in_canvas,width=2,outline=self.color)
                 #self.edge_change = self.canvas.create_line(x1_in_canvas, y0_in_canvas, x1_in_canvas, y1_in_canvas, fill='yellow', width=2)
            if self.idx == 3 : #DC
                 self.rect = self.canvas.create_rectangle(x0_in_canvas, y0_in_canvas,x1_in_canvas, y1_in_canvas,width=2,outline=self.color)
                 #self.edge_change = self.canvas.create_line(x0_in_canvas, y1_in_canvas, x1_in_canvas, y1_in_canvas, fill='yellow', width=2)

    def move_side(self,x,y,x_offset,y_offset,scale):
        if self.state_box ==1:
            
            x_in_im, y_in_im = self._convert_to_image_coodinates(x,y,x_offset,y_offset,scale)

            self.canvas.delete(self.rect)
            #self.canvas.delete(self.edge_change)

            x0_in_canvas, y0_in_canvas = self._convert_to_canvas_coodinates(self.corners[0],self.corners[1],x_offset,y_offset,scale)
            x1_in_canvas, y1_in_canvas = self._convert_to_canvas_coodinates(self.corners[2],self.corners[3],x_offset,y_offset,scale)

            if self.idx == 0 : #AD
                 self.rect = self.canvas.create_rectangle(x, y0_in_canvas,x1_in_canvas, y1_in_canvas,width=2,outline=self.color)
                 #self.edge_change = self.canvas.create_line(x, y0_in_canvas, x, y1_in_canvas, fill='yellow', width=2)
                 self.corners[0] = x_in_im
            if self.idx == 1 : #AB
                 self.rect = self.canvas.create_rectangle(x0_in_canvas, y,x1_in_canvas, y1_in_canvas,width=2,outline=self.color)
                 #self.edge_change = self.canvas.create_line(x0_in_canvas, y, x1_in_canvas, y, fill='yellow', width=2)
                 self.corners[1] = y_in_im
            if self.idx == 2 : #BC
                 self.rect = self.canvas.create_rectangle(x0_in_canvas, y0_in_canvas,x, y1_in_canvas,width=2,outline=self.color)
                 #self.edge_change = self.canvas.create_line(x, y0_in_canvas, x, y1_in_canvas, fill='yellow', width=2)
                 self.corners[2] = x_in_im
            if self.idx == 3 : #DC
                 self.rect = self.canvas.create_rectangle(x0_in_canvas, y0_in_canvas,x1_in_canvas, y,width=2,outline=self.color)
                 #self.edge_change = self.canvas.create_line(x0_in_canvas, y, x1_in_canvas, y, fill='yellow', width=2)
                 self.corners[3] = y_in_im

    def stop_side(self,x,y,x_offset,y_offset,scale):
          if self.state_box ==1:
               x_in_im, y_in_im = self._convert_to_image_coodinates(x,y,x_offset,y_offset,scale)
            
               self.canvas.delete(self.rect)
               #self.canvas.delete(self.edge_change)
               #self.edge_change = None

               x0_in_canvas, y0_in_canvas = self._convert_to_canvas_coodinates(self.corners[0],self.corners[1],x_offset,y_offset,scale)
               x1_in_canvas, y1_in_canvas = self._convert_to_canvas_coodinates(self.corners[2],self.corners[3],x_offset,y_offset,scale)

               if self.idx == 0 : #AD
                    self.rect = self.canvas.create_rectangle(x, y0_in_canvas,x1_in_canvas, y1_in_canvas,width=2,outline=self.color)
                    self.corners[0] = x_in_im
               if self.idx == 1 : #AB
                    self.rect = self.canvas.create_rectangle(x0_in_canvas, y,x1_in_canvas, y1_in_canvas,width=2,outline=self.color)
                    self.corners[1] = y_in_im
               if self.idx == 2 : #BC
                    self.rect = self.canvas.create_rectangle(x0_in_canvas, y0_in_canvas,x, y1_in_canvas,width=2,outline=self.color)
                    self.corners[2] = x_in_im
               if self.idx == 3 : #DC
                    self.rect = self.canvas.create_rectangle(x0_in_canvas, y0_in_canvas,x1_in_canvas, y,width=2,outline=self.color)
                    self.corners[3] = y_in_im
            
               return self.corners
          else:
             return []

     