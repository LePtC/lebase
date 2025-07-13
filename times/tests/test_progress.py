from lebase.times.progress import Progress
import time


def test_progress_basic():
    with Progress(3, "测试进度") as pr:
        for i in range(3):
            pr.tik(f"step {i}")
            time.sleep(0.01)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
