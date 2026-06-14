"""
Computer Use 框架演示脚本

运行前先安装依赖:
    pip install -r computer_use/requirements.txt

用法:
    python demo.py          # 基本演示
    python demo.py --task "打开记事本并输入 Hello"   # 自定义任务
"""

import argparse
import sys
import time

sys.path.insert(0, ".")

from computer_use import Controller, ComputerUseAgent
from computer_use.agent import MockAgent


def demo_basic():
    """演示 Controller 的基本能力"""
    ctrl = Controller()

    print("=== 屏幕信息 ===")
    print(f"屏幕尺寸: {ctrl.screen_size()}")
    print(f"鼠标位置: {ctrl.position().to_tuple()}")

    print("\n=== 3 秒后截屏 ===")
    time.sleep(3)
    import io
    from PIL import Image

    data = ctrl.screenshot()
    img = Image.open(io.BytesIO(data))
    img.save("screenshot_demo.png")
    print("截图已保存: screenshot_demo.png")


def demo_actions():
    """演示自动化动作（需谨慎运行）"""
    ctrl = Controller()

    print("=== 动作演示 ===")
    print("3 秒后开始执行...")
    time.sleep(3)

    actions = [
        {"type": "cursor_position", "params": {}},
        {"type": "mouse_move", "params": {"x": 500, "y": 300}},
        {"type": "wait", "params": {"seconds": 1}},
        {"type": "cursor_position", "params": {}},
    ]

    results = ctrl.execute_batch(actions)
    for r in results:
        status = "OK" if r.success else "FAIL"
        print(f"  {r.action_type.value}: {status} {r.data or ''}")


def demo_agent():
    """演示 Agent 模式（Mock 模式，不会真的调用 AI）"""
    from computer_use import Controller
    from computer_use.agent import MockAgent

    ctrl = Controller()
    print(f"当前鼠标位置: {ctrl.position().to_tuple()}")

    actions = [
        {"type": "cursor_position", "params": {}},
        {"type": "mouse_move", "params": {"x": 100, "y": 100}},
        {"type": "cursor_position", "params": {}},
    ]

    agent = MockAgent(actions, ctrl)
    print(f"\n执行任务: 移动鼠标到 (100, 100)")
    print("3 秒后开始...")
    time.sleep(3)

    results = agent.run("移动鼠标到 (100, 100)")
    for r in results:
        print(f"  [{r.action_type.value}] success={r.success} data={r.data}")


def main():
    parser = argparse.ArgumentParser(description="Computer Use 演示")
    parser.add_argument(
        "--mode",
        choices=["basic", "actions", "agent"],
        default="basic",
        help="演示模式 (默认: basic)",
    )
    args = parser.parse_args()

    if args.mode == "basic":
        demo_basic()
    elif args.mode == "actions":
        demo_actions()
    elif args.mode == "agent":
        demo_agent()


if __name__ == "__main__":
    main()