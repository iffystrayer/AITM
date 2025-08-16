import sys,os
import requests
from myapp.models import User
import json
from django.db import models
import asyncio

def badly_formatted_function(x,y,z):
    if x>0:
        result=x+y+z
        return result
    else:
        return None

class PoorlyFormattedClass:
    def __init__(self,name,age):
        self.name=name
        self.age=age
    
    def get_info(self):
        return f"{self.name} is {self.age} years old"
    
    def process_data(self,data):
        if data:
            processed=[]
            for item in data:
                if item['status']=='active':
                    processed.append(item)
            return processed
        return []

async def async_function(param1,param2):
    result=await some_async_operation(param1,param2)
    return result

# Some trailing whitespace issues   
def function_with_whitespace():   
    x = 1    
    y = 2   
    return x + y    
