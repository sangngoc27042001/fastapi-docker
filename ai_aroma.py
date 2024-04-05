import datetime
import time
import asyncio

lock = asyncio.Lock()

class AIAroma():
    def __init__(self):
        self.waiting_time = 10
        self.dict = {}
    async def on_message(self, message_data):
        id = message_data['id']
        print(f"recieve {id}")
        
        async with lock:
            if id in self.dict.keys():
                self.dict[id].append(message_data)
            else:
                self.dict[id] = [message_data]

        length_befor = len(self.dict[id])
        print(f"length_befor: {length_befor}")
        await asyncio.sleep(self.waiting_time)
        length_after = len(self.dict[id])
        print(f"length_after: {length_after}")
        
        if length_after>length_befor:
            return {
                'should_response':False
            }
        else:
            #TODO
            async with lock:
                return {
                    'should_response':True,
                    'message':self.dict.pop(id)
                }
            
    