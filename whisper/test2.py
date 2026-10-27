import os
# Force disable proxy for local connections to avoid connection issues
os.environ["NO_PROXY"] = "127.0.0.1,localhost"

from ollama import Client

# Initialize the client pointing to your local Ollama instance
client = Client(host='http://127.0.0.1:11434')

dialogue = "销售B：你好，王总。客户A：你好。听说你们最近新出了一套针对企业数据清洗的系统，我想了解一下具体的合作方案。销售B：好的，王总，非常感谢您对我们产品的关注！为了能安排我们最资深的行业专家跟您对接，并为您定制一份专属的演示方案，方便先请教一下贵公司的全称吗？客户A：暂时不方便说。销售B：好的。我们之前接触过不少科技创新企业，确实有很多高价值的非结构化数据需要处理。那王总，稍后我把详细的产品白皮书和行业案例发到您的微信上，同时也方便把您的电话号码留给我吗？这样专家在致电前可以先跟您预约时间。客户A：没问题，我的手机号是 138-1234-5678，这也是我的微信同号，你直接加我就行。销售B：好的，王总，电话 13812345678 我已经记下了。我这就添加您的微信，并把相关资料发过去，请您注意查收。"
try:
    
    response = client.chat(
        model='qwen2.5',  # Use the vision-enabled tag
        messages=[
            {
                'role': 'user',
                'content': f'你是一个专业的销售人员，你善于从和客户的沟通中总结信息。请根据对话:{dialogue},提取出来客户的：客户名称(客户的真实姓氏或称呼)、公司名称、电话号码。输出为json格式。 如果没有找到相关信息，请使用 【--】',
            }
        ]
    )    
    print(response.message)

except Exception as e:
    print(f"Error: {e}")