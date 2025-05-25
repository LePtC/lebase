"""
lefac 项目统一使用这样的接口：from lebase.log import log，然后函数名都和标准 logger 保持相同
消息既会被打印，又会被写入到 downloads/nosync/log 目录下
打印时是彩色信息，写入时是 json 结构化日志
日志按来源模块分流存放，并根据体量给文件名添加按日或月的后缀，避免单文件体积过大
在实现上目前选择 loguru，据说多线程和性能方面表现好

lefac 的主要配置信息都存放在 appdata/lefac 目录（对 win 和 linux 都适用）
lefac 有一个 nosync 目录，统一位于 downloads/nosync（PC 和云服务器都是），主要用来保管本机 log，不会和其它任何节点同步
对于 PC（lefac 不在 dowloads 下），还会有一个位于 Q/pcsync，用来存放体积大的不想和云同步（但会和其它 PC 同步）的文件（例如 bykzip 和 bykfin）

250525 prompt2：

下面是一个python项目底层所使用的log模块，作用是在打印的同时也将日志写入到文件中，文件名取决于入口py文件名和当前的日期。
目前发现存在一个问题：当程序启动后，文件名会被锁定在当前日期的文件名上，即使程序持续运行了很多天，输出到的日志文件名日期仍然保持不变。
请你帮我改进一下这个模块，实现当程序运行到新的日期后，自动写往新的日期命名的日志文件。
请你告诉我你是如何理解和分析的，告诉我代码中哪些地方要做什么样的修改，而不要一次性给我所有代码。
"""

import os
import sys

from loguru import logger


def get_log_filename(_path):
    """
    自动判断当前运行环境：
      - 如果是通过 .py 调用，则使用 "lefac逻辑" 来生成日志文件名；
        - 若包含 'lefac'，提取 lefac 后续路径的所有目录及文件名（不含扩展名）拼接；
        - 若不包含 lefac，只拼接上一层目录名和文件名（不含扩展名）。
      - 如果是通过 Jupyter Notebook 调用，
        则传入 os.path.abspath(sys.argv[0]) 会识别成 site-packages-ipykernel_launcher
        需重新识别当前 Notebook 名称（去掉 .ipynb）来生成日志文件名。
    """

    # 判断是否在 Jupyter Notebook 环境
    # if "ipykernel" in sys.modules:
    try:
        # 尝试调用 get_ipython()，如果存在说明是交互式环境
        shell = get_ipython().__class__.__name__
        print("是交互式环境")
        path = os.getcwd() + "\\ipykernel.ipynb"  # TODO GPT提供的方法都无法识别ipynb笔记本名
    except Exception:
        # 当前是非 jupyter 环境
        if _path:
            path = _path
        else:
            path = "未识别文件名.py"

    # ---- 情况2：普通 .py 脚本 ----
    # 将可能的 Windows 路径分隔符转为统一的 '/'
    normalized_path = path.replace("\\", "/")
    parts = normalized_path.split("/")

    # 判断是否存在 'lefac' 目录
    if "lefac" in parts:
        # 找到 'lefac' 在列表中的位置
        idx = parts.index("lefac")
        # 取出 lefac 之后的所有目录及文件
        after_lefac = parts[idx + 1 :]  # 比如 ['bbb', 'ccc', 'myfun.py']
        if not after_lefac:
            # 理论上不会出现，但如果 lefac 后面没有任何内容，可以自行定义处理
            return "unknown"

        # 拆分最后一个文件名
        *dirs, filename = after_lefac
        base, _ = os.path.splitext(filename)

        # 将目录和基名用 '-' 拼起来，并加上 .log
        return "-".join(dirs + [base])
    else:
        # 如果不包含 lefac，则只获取上一层目录名 + 文件名
        if len(parts) < 2:
            # 如果整条路径可能只有文件名，如 "myfun.py"
            base, _ = os.path.splitext(parts[-1])
            return base
        else:
            # 获取最后一个目录名
            parent_dir = parts[-2]
            # 获取文件名（去掉后缀）
            filename = parts[-1]
            base, _ = os.path.splitext(filename)
            return "-".join([parent_dir, base])


# 获取调起Python程序的__main__文件的文件名
main_file_name = get_log_filename(os.path.abspath(sys.argv[0]))
log_dir = os.path.join(os.path.expanduser("~"), "downloads", "nosync", "log")
os.makedirs(log_dir, exist_ok=True)
# current_date = datetime.now().strftime("%y%m%d")  # 不再提前生成一次性日期字符串，而是rotate
log_file_tpl = os.path.join(log_dir, f"{main_file_name}.{{time:YYMMDD}}.log")


# 移除 loguru 默认处理器
logger.remove()


def custom_format(record):
    file_path = record["file"].path
    file_name = file_path.split("lefac\\")[-1]

    log_format = (
        f"<light-magenta>{{time:MM/DD HH:mm:ss}}</light-magenta> "
        f"<level>{{level}}\t</level> "
        f"<light-cyan>[{file_name}:{{line}}]</light-cyan> "
        f"{{function}}: <level>{{message}}</level>\n"
    )
    return log_format


# 连续输出时简洁版
short_format = "{message}"


# 定义过滤函数，根据 extra 中的 template 值决定使用哪个 Handler
def default_filter(record):
    return record["extra"].get("template", "default") == "default"


def short_filter(record):
    return record["extra"].get("template", "default") == "short"


logger.add(sys.stderr, format=custom_format, level="DEBUG", colorize=True, filter=default_filter)
# logger.add(log_file_path, format="", level="INFO", serialize=True)  # serialize 有点信息过于丰富…
logger.add(log_file_tpl, rotation="00:00", enqueue=True, format=custom_format, level="INFO", serialize=False, filter=default_filter)


# 添加使用 short_format 的处理器（输出到屏幕和日志文件）
logger.add(sys.stderr, format=short_format, level="DEBUG", colorize=True, filter=short_filter)
logger.add(log_file_tpl, rotation="00:00", enqueue=True, format=short_format, level="INFO", serialize=False, filter=short_filter)


# 添加 warn 方法作为 warning 的别名
logger.warn = logger.warning


# 设置额外的上下文信息，用于屏幕输出格式
def set_context(template="default"):
    """
    设置日志上下文，并允许指定模板：
      template="default" 使用 custom_format (默认)
      template="short"  使用 short_format
    """
    frame = sys._getframe(1)
    return logger.bind(filename=os.path.basename(frame.f_code.co_filename), line=frame.f_lineno, template=template)


log = set_context()
log.warn = log.warning

# 其它模块可以通过传入 template 参数来使用 short_format 格式
log0 = set_context(template="short")
log0.warn = log0.warning


# ----------------------------
# css utils
# ----------------------------


def bool_color(flag: bool) -> str:
    """将布尔值转换为带 ANSI 颜色的字符串。``True`` 为绿色，``False`` 为红色。"""
    return f"\033[32m{flag}\033[39m" if flag else f"\033[31m{flag}\033[39m"


if __name__ == "__main__":

    # 测试示例
    path1 = "aaa/lefac/bbb/ccc/myfun.py"
    path2 = "xxx/zzz/myfun.py"

    print(get_log_filename(path1))  # 期望输出: bbb-ccc-myfun.log
    print(get_log_filename(path2))  # 期望输出: zzz-myfun.log

    # ----------------------------

    log.debug("lebase.log init success")

    def test():
        log.trace("Executing program")
        log.debug("Processing data...")
        log.info("Server started successfully.")
        log.success("Data processing completed successfully.")

    test()
    log.warning("Invalid configuration detected.")
    log.warn("Invalid configuration detected.")
    log.error("Failed to connect to the database.")
    log.critical("Unexpected system error occurred. Shutting down.")

    log0.debug("简易模式 Processing data...")
    log0.info("简易模式 Server started successfully.")
    log0.warn("简易模式 Invalid configuration detected.")
    log0.error("简易模式 Failed to connect to the database.")
    log0.critical("简易模式 Unexpected system error occurred. Shutting down.")
