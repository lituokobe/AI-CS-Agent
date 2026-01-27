import argparse

def start_gateway_service():
    """启动网关服务"""
    from models.ai_gateway_service import start_gateway_service
    start_gateway_service()

def start_ai_service():
    """启动AI服务"""
    from models.ai_service import start_dynamic_service
    start_dynamic_service()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='启动AI外呼系统服务')
    parser.add_argument('service', choices=['gateway', 'ai'], help='要启动的服务')

    args = parser.parse_args()

    if args.service == 'gateway':
        start_gateway_service()
    elif args.service == 'ai':
        start_ai_service()