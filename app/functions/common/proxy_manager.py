import requests
import random
import time

CLASH_API = "http://127.0.0.1:9090"
PROXY_GROUP = "PROXY"

PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890"
}

TEST_URL = "https://httpbin.org/ip"
TIMEOUT = 8
MAX_TEST_PER_NODE = 1


class ProxyManager:
    def __init__(self):
        self.session = requests.Session()

    # ========== Clash API ==========
    def get_nodes(self):
        try:
            r = requests.get(f"{CLASH_API}/proxies", timeout=5)
            data = r.json()
            return data["proxies"][PROXY_GROUP]["all"]
        except Exception as e:
            print("获取节点失败:", e)
            return []

    def switch_node(self, node_name):
        try:
            url = f"{CLASH_API}/proxies/{PROXY_GROUP}"
            requests.put(url, json={"name": node_name}, timeout=5)
            print(f"切换节点成功: {node_name}")
            return True
        except Exception as e:
            print("切换节点失败:", e)
            return False

    # ========== 节点可用性测试 ==========
    def test_proxy(self):
        try:
            r = self.session.get(
                TEST_URL,
                proxies=PROXIES,
                timeout=TIMEOUT
            )
            return r.status_code == 200
        except:
            return False

    # ========== 自动找可用节点 ==========
    def find_working_node(self):
        nodes = self.get_nodes()
        random.shuffle(nodes)

        print(f"开始测试节点，总数: {len(nodes)}")

        for node in nodes:
            print(f"测试节点: {node}")
            self.switch_node(node)
            time.sleep(1)

            for _ in range(MAX_TEST_PER_NODE):
                if self.test_proxy():
                    print(f"可用节点: {node}")
                    return True

        print("没有找到可用代理节点")
        return False

    # ========== 带代理请求 ==========
    def request(self, method, url, **kwargs):
        if not self.test_proxy():
            print("当前节点不可用，自动寻找新节点...")
            if not self.find_working_node():
                raise RuntimeError("没有可用代理节点")

        return self.session.request(
            method,
            url,
            proxies=PROXIES,
            timeout=TIMEOUT,
            **kwargs
        )
