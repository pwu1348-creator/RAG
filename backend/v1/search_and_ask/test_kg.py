
import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8002/api/v1/search"
TIMEOUT = 10

class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_result(test_name: str, success: bool, message: str = ""):
    status = f"{Color.GREEN}✓ PASS{Color.END}" if success else f"{Color.RED}✗ FAIL{Color.END}"
    print(f"{status} | {test_name}")
    if message:
        print(f"      {message}")

def test_kg_status() -> bool:
    print(f"\n{Color.BLUE}[测试 1] KG 状态检查{Color.END}")
    try:
        response = requests.get(
            f"{BASE_URL}/kg/status",
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            print_result(
                "GET /kg/status",
                True,
                f"后端: {data.get('kg_backend')}, 启用: {data.get('kg_enabled')}"
            )
            return data.get('kg_enabled', False)
        else:
            print_result("GET /kg/status", False, f"状态码: {response.status_code}")
            return False
    except Exception as e:
        print_result("GET /kg/status", False, str(e))
        return False

def test_entity_extraction() -> bool:
    print(f"\n{Color.BLUE}[测试 2] 实体关系提取{Color.END}")
    try:
        payload = {
            "doc_id": "test_doc_001",
            "kb_id": "test_kb_001",
            "content": "张三是人工智能工程师，在科技公司工作。他专注于知识图谱和自然语言处理研究。",
            "chunk_size": 2000
        }
        
        response = requests.post(
            f"{BASE_URL}/kg/extract/sync",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            entities = data.get('entity_count', 0)
            relations = data.get('relation_count', 0)
            print_result(
                "POST /kg/extract/sync",
                True,
                f"提取实体: {entities}, 关系: {relations}"
            )
            if entities > 0:
                print(f"      实体: {[e['name'] for e in data.get('entities', [])]}")
            return entities > 0
        else:
            print_result(
                "POST /kg/extract/sync",
                False,
                f"状态码: {response.status_code}, 内容: {response.text[:100]}"
            )
            return False
    except requests.Timeout:
        print_result(
            "POST /kg/extract/sync",
            False,
            "超时（LLM API 可能响应慢）"
        )
        return False
    except Exception as e:
        print_result("POST /kg/extract/sync", False, str(e))
        return False

def test_entity_search() -> bool:
    print(f"\n{Color.BLUE}[测试 3] 实体搜索{Color.END}")
    try:
        payload = {
            "name": "张三",
            "limit": 10
        }
        
        response = requests.post(
            f"{BASE_URL}/kg/search/entity",
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            print_result(
                "POST /kg/search/entity",
                True,
                f"找到 {total} 个实体"
            )
            return True
        else:
            print_result(
                "POST /kg/search/entity",
                False,
                f"状态码: {response.status_code}"
            )
            return False
    except Exception as e:
        print_result("POST /kg/search/entity", False, str(e))
        return False

def test_multihop_search() -> bool:
    print(f"\n{Color.BLUE}[测试 4] 多跳关联查询{Color.END}")
    try:
        payload = {
            "entity_name": "张三",
            "hops": 2,
            "limit": 50
        }
        
        response = requests.post(
            f"{BASE_URL}/kg/search/multihop",
            json=payload,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            entity_count = len(data.get('entities', []))
            relation_count = len(data.get('relations', []))
            print_result(
                "POST /kg/search/multihop",
                True,
                f"实体: {entity_count}, 关系: {relation_count}"
            )
            return True
        else:
            print_result(
                "POST /kg/search/multihop",
                False,
                f"状态码: {response.status_code}"
            )
            return False
    except Exception as e:
        print_result("POST /kg/search/multihop", False, str(e))
        return False

def test_qa_with_kg() -> bool:
    print(f"\n{Color.BLUE}[测试 5] 问答（使用 KG）{Color.END}")
    try:
        payload = {
            "query": "谁是人工智能工程师？",
            "knowledge_base_id": "test_kb_001",
            "use_kg": True,
            "kg_weight": 0.3,
            "top_k": 5
        }
        
        response = requests.post(
            f"{BASE_URL}/ask",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            print_result(
                "POST /ask (use_kg=True)",
                True,
                f"回答长度: {len(answer)} 字符"
            )
            return len(answer) > 0
        else:
            print_result(
                "POST /ask (use_kg=True)",
                False,
                f"状态码: {response.status_code}"
            )
            return False
    except requests.Timeout:
        print_result(
            "POST /ask (use_kg=True)",
            False,
            "超时（LLM 或检索可能需要较长时间）"
        )
        return False
    except Exception as e:
        print_result("POST /ask (use_kg=True)", False, str(e))
        return False

def test_connectivity() -> bool:
    print(f"\n{Color.BLUE}[测试 0] 基本连接{Color.END}")
    try:
        response = requests.get(
            f"{BASE_URL}/../kb_list",
            timeout=TIMEOUT
        )
        if response.status_code in [200, 404]:
            print_result("连接 QA Service", True, f"服务地址: {BASE_URL}")
            return True
        else:
            print_result("连接 QA Service", False, f"状态码: {response.status_code}")
            return False
    except requests.ConnectionError:
        print_result(
            "连接 QA Service",
            False,
            f"无法连接，请检查服务是否运行在 {BASE_URL}"
        )
        return False
    except Exception as e:
        print_result("连接 QA Service", False, str(e))
        return False

def main():
    print(f"{Color.BLUE}{'='*60}")
    print(f"知识图谱功能测试 - PengPeng RAG System")
    print(f"{'='*60}{Color.END}")
    print(f"测试地址: {BASE_URL}\n")
    
    results = {}
    
    results['connectivity'] = test_connectivity()
    if not results['connectivity']:
        print(f"\n{Color.RED}错误: 无法连接到服务！请确保：{Color.END}")
        print("1. QA Service 已启动: python main.py")
        print("2. 服务运行地址正确: http://localhost:8002")
        return 1
    
    results['kg_status'] = test_kg_status()
    if not results['kg_status']:
        print(f"\n{Color.RED}错误: KG 服务未启用！请检查：{Color.END}")
        print("1. KG_ENABLED=True")
        print("2. 依赖已安装: pip install -r requirements.txt")
        return 1
    
    results['extraction'] = test_entity_extraction()
    
    results['search'] = test_entity_search()
    
    results['multihop'] = test_multihop_search()
    
    results['qa'] = test_qa_with_kg()
    
    print(f"\n{Color.BLUE}{'='*60}")
    print("测试总结")
    print(f"{'='*60}{Color.END}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"通过: {Color.GREEN}{passed}/{total}{Color.END}")
    
    for test_name, result in results.items():
        status = f"{Color.GREEN}✓{Color.END}" if result else f"{Color.RED}✗{Color.END}"
        print(f"  {status} {test_name}")
    
    if passed == total:
        print(f"\n{Color.GREEN}🎉 所有测试通过！知识图谱功能正常运行。{Color.END}")
        return 0
    else:
        print(f"\n{Color.YELLOW}⚠️  部分测试失败，请查看上面的错误信息。{Color.END}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
