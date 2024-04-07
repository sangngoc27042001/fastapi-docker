from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain import hub
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
import json
from langchain_community.chat_message_histories.mongodb import MongoDBChatMessageHistory

from typing import Optional, List, Literal
import re
from dotenv import load_dotenv
import os
load_dotenv()
import asyncio
import pymongo

client = pymongo.MongoClient(os.getenv('MONGODB_CONNECTION_STRING'))
database = client["aroma_bakery"]

# AI IMPLEMENTATION #

data = json.load(open('chickendata.json', 'r'))
product_list = list(data.keys())
Argument = Literal['1']
Argument.__args__ = tuple(product_list)

class ProductItem(BaseModel):
    name: Optional[Argument] = Field(description="tên sản phẩm")
    quantity: Optional[int] = Field(description="số lượng muốn mua")

class Serve(BaseModel):
    # customer_name: Optional[str] = Field(description="tên của khách hàng")
    customer_phone_number: Optional[str] = Field(description="số điện thoại của khách hàng (không phải số điện thoại của Aroma)")
    order: Optional[List[ProductItem]] = Field(description="Một đơn hàng chứa danh sách các sản phẩm.")

class CheckInventory(BaseModel):
    order: List[ProductItem] = Field(description="Một đơn hàng chứa danh sách các sản phẩm.")

@tool("serve", args_schema=Serve,
      # return_direct=True #Will return the direct result in string form
      )
def serve(customer_phone_number="", order=[]):
    """được sử dụng khi khách hàng muốn mua bánh hoặc order sản phẩm"""
    if "918815325" in customer_phone_number:
        if order!=[]:
            return "Bạn hay cung cấp đầy đủ thông tin về số điện thoại"
        return ""      
    
    if all([customer_phone_number!="", order!=[] and order!=None]):
        # return check_inventory(customer_phone_number, order)
        if re.match(r'[+]?[\d\s]{9,20}', customer_phone_number) == None:
            return "Số điện thoại không hợp lệ, vui lòng nhập lại."
        return trigger(customer_phone_number, order)
    elif all([customer_phone_number=="", order==[] or order==None]):
        return ""
    
    response = f'Bạn hay cung cấp đầy đủ thông tin về {"số điện thoại" if customer_phone_number=="" else ""}, {"đơn hàng (loại bánh + số lượng)" if order==[] else ""}.'
    return response

def check_inventory(customer_phone_number, order=[]):
    """"""
    deficient_product_list = []
    order = {x.name:x.quantity for x in order}
    print(order)
    for product in list(order.keys()):
        if product not in product_list:
            return f"sản phẩn {product} không tồn tại. xin hãy chọn một trong các sản phẩm sau (nêu kèm số lượng): {data.keys()}"
        if order[product]>data[product]:
            deficient_product_list.append(product)
    if deficient_product_list==[]:
        return trigger(customer_phone_number, order)
    else:
        return "Hiện tại:\n" + '\n'.join([f"Bánh {x} chỉ còn {data[x]} chiếc" for x in deficient_product_list]) +"\n Phiền bạn nhập lại số lượng sao cho phù hợp bạn ha ^^."


def trigger(customer_phone_number, order):
    """"""
    result = database['order'].insert_one(
        {'phone_number':customer_phone_number,
         'products': [dict(x) for x in order]}
    )
    print(f"add order {result}")
    return f"Order thành công, chờ nghe điện thoại.\n gửi lại cho khách như sau:\nThông tin đơn hàng:\n số điện thoại: {customer_phone_number} \n danh sách sản phẩm: {order}"

@tool("send_menu")
def send_menu():
    """Được sử dụng khi khách hỏi về menu, thực đơn, quán có món gì, bánh gì ngon."""
    return f"Aroma xin gửi thực đơn ạ: \n {[x for x in data]}"

tools = [
    serve,
    send_menu
]

prompt = hub.pull("hwchase17/openai-tools-agent")

system_template ="""

Bạn là một người trợ lý ảo có nhiệm vụ nhận order của khách hàng cho tiệm bánh Aroma.

Một vài thông tin về tiệm bánh Aroma:
- Địa chỉ: 325a Đ. Điện Biên Phủ, Phường 15, Bình Thạnh, Thành phố Hồ Chí Minh [https://maps.app.goo.gl/6Y7jEWVKbu1Rs2Ww8]
- Số điện thoại (phone): 0918815325

Tuân thử những điều sau:
1/ Giới thiệu mình là trợ lý ảo của tiệm bánh Aroma Bakery
2/ Nếu khách hàng muốn mua bánh, sử dụng `serve` ngay lập tức.
3/ Nếu khách hàng muốn xem thực đơn, sử dụng `send_menu` ngay lập tức.
"""
prompt.messages[0] = prompt.messages[0].from_template(system_template)

llm = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0, openai_api_key = os.getenv('OPENAI_API_KEY'))

agent = create_openai_functions_agent(
    tools = tools,
    llm = llm,
    prompt = prompt
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

def trim_messages(history_object):
    stored_messages = history_object.messages
    if len(stored_messages) <= int(os.getenv('NO_MESSAGES_REMEMBER')):
        return history_object

    history_object.clear()

    for message in stored_messages[-int(os.getenv('NO_MESSAGES_REMEMBER')):]:
        history_object.add_message(message)

    return history_object

agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor,
        lambda session_id: trim_messages(MongoDBChatMessageHistory(
            session_id=session_id,
            connection_string=os.getenv('MONGODB_CONNECTION_STRING'),
            database_name="aroma_bakery",
            collection_name="chat_history",
        )),
        input_messages_key="input",
        history_messages_key="chat_history",
    )

print("[INFO] Load AI successfully")
# AI IMPLEMENTATION #



lock = asyncio.Lock()

class AIAroma():
    def __init__(self):
        self.waiting_time = int(os.getenv('WAIT_FOR_RESPONSE'))
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
            input_message = f"Xin chào, tôi tên là {message_data['sender_name']}.\n" + '\n'.join([x['content'] for x in self.dict[id]])
            output = agent_with_chat_history.invoke(
                {"input": input_message},
                config={"configurable": {"session_id": id}},
            )['output']
            async with lock:
                self.dict.pop(id)
                print(f"{id}: {input_message}")
                print(f"AI reply to {id}: {output}")
                return {
                    'should_response':True,
                    'message':output
                }
            
    