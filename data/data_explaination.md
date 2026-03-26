## Knowledge
`answer_type` : 1单轮回答 2多轮回答',  
`answer` : 单轮回答时是话术json，
```python
[
    {
        "content":'',
        "action": 1, # 0等待用户回复 1挂断 3跳转主流程
        "next": -1, # -1原主线节点 -2原主线流程  others指定主线流程
        "master_process_id": "id_name"
    },
    {} 
]
```  
多轮回答时 是知识库流程的knowledge_process_id',

## Base Node Transfer Node
`action` : 1挂断 2跳转下一主线流程 3跳转指定主线流程  
`master_process_id` : id_name

## Knowledge Node Transfer Node
`action` : 0挂断 1跳转下一主线流程 3跳转指定主线流程  
`master_process_id` : -1原主线节点 -2原主线流程  others指定主线流程id_name 

## Global config
`context_type` : 1客户无应答模块 2ai未识别模块 3噪音处理模块  
`answer` : 
```python
[
    {
        "content":'',
        "action": 1, # 1等待用户回复  2挂断  3跳转主流程,
        "next": -1, # -1原主线节点 -2原主线流程  3指定主线流程
        "master_process_id": "id_name"
    },
    {} 
]
```
