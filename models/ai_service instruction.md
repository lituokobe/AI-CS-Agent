1. run ai_service.py
2. run ai_gateway_service.py
3. In postman, start the model by POST `http://127.0.0.1:5001/gateway/model/start`  
Make sure in Headers: Content-Type: application/json   
The body is (using default data): 
```
{
  "model_id": "my_test_model",
  "config_data": {},
  "expire_time": 1836150400,
  "only_delay": false
}
```
4. To check weather the model is active (model status): GET `http://127.0.0.1:5002/model/status?model_id=my_test_model`
5. Test the keyword matching service with 
  - `POST http://127.0.0.1:5001/gateway/keyword_match`
  - `POST http://192.168.0.143:5001/gateway/keyword_match`
The body is (using default data): 
```
{"keywords": ["^你好"], "sentence": "你好啊"}
```
6. Talk to the agent with POST `http://127.0.0.1:5001/gateway/conversation`  
The body is (using default data): 
```
{
  "call_id": "call_001",
  "task_id": "task_001",
  "model_id": "my_test_model",
  "backstop_model": "my_test_model",
  "current_input": "你说什么",
  "original_number": "13800138000",
  "not_answer_wait_seconds": 5,
  "is_customer_max_answer_seconds": 0,
  "customer_max_answer_seconds": 0,
  "vad_time": 0,
  "check_noise": 0
}
```