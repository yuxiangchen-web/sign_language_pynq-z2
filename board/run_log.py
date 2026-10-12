"""保存带环境信息的真实测试日志；调用方必须明确标注执行模式。"""

import json
import platform
from datetime import datetime, timezone
from pathlib import Path


def write_json(path, result):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {"recorded_at": datetime.now(timezone.utc).isoformat(),
              "platform": platform.platform(), "python": platform.python_version(), **result}
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False),
                    encoding="utf-8")
    return record
