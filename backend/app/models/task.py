"""
任务状态管理
用于跟踪长时间运行的任务（如图谱构建）
"""

import json
import os
import uuid
import threading
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from ..utils.locale import t


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"          # 等待中
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败


@dataclass
class Task:
    """任务数据类"""
    task_id: str
    task_type: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    progress: int = 0              # 总进度百分比 0-100
    message: str = ""              # 状态消息
    result: Optional[Dict] = None  # 任务结果
    error: Optional[str] = None    # 错误信息
    metadata: Dict = field(default_factory=dict)  # 额外元数据
    progress_detail: Dict = field(default_factory=dict)  # 详细进度信息
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "progress": self.progress,
            "message": self.message,
            "progress_detail": self.progress_detail,
            "result": self.result,
            "error": self.error,
            "metadata": self.metadata,
        }


class TaskManager:
    """
    任务管理器
    线程安全的任务状态管理，持久化到文件
    """
    
    _instance = None
    _lock = threading.Lock()
    _STORAGE_FILENAME = "tasks.json"
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._tasks: Dict[str, Task] = {}
                    cls._instance._task_lock = threading.Lock()
                    cls._instance._storage_path: Optional[str] = None
                    cls._instance._last_mtime: float = 0
        return cls._instance
    
    def init_storage(self, storage_dir: str):
        """初始化存储目录并加载已有任务"""
        self._storage_path = os.path.join(storage_dir, self._STORAGE_FILENAME)
        os.makedirs(storage_dir, exist_ok=True)
        self._load_from_disk()
    
    def _needs_reload(self) -> bool:
        """检查文件是否被其他进程修改过"""
        if not self._storage_path or not os.path.exists(self._storage_path):
            return False
        try:
            mtime = os.path.getmtime(self._storage_path)
            return mtime > self._last_mtime
        except Exception:
            return False
    
    def _serialize_tasks(self) -> Dict[str, dict]:
        """序列化所有任务为可 JSON 的字典"""
        return {
            tid: {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": task.status.value,
                "created_at": task.created_at.isoformat(),
                "updated_at": task.updated_at.isoformat(),
                "progress": task.progress,
                "message": task.message,
                "result": task.result,
                "error": task.error,
                "metadata": task.metadata,
                "progress_detail": task.progress_detail,
            }
            for tid, task in self._tasks.items()
        }
    
    def _deserialize_task(self, data: dict) -> Task:
        """反序列化一个任务"""
        return Task(
            task_id=data["task_id"],
            task_type=data["task_type"],
            status=TaskStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            progress=data.get("progress", 0),
            message=data.get("message", ""),
            result=data.get("result"),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
            progress_detail=data.get("progress_detail", {}),
        )
    
    def _persist(self):
        """写入任务到磁盘"""
        if not self._storage_path:
            return
        try:
            with self._task_lock:
                data = self._serialize_tasks()
            tmp = self._storage_path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self._storage_path)
        except Exception:
            pass
    
    def _load_from_disk(self):
        """从磁盘加载任务"""
        if not self._storage_path or not os.path.exists(self._storage_path):
            return
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            with self._task_lock:
                self._tasks = {}
                for tid, task_data in data.items():
                    self._tasks[tid] = self._deserialize_task(task_data)
            self._last_mtime = os.path.getmtime(self._storage_path)
        except Exception:
            self._tasks = {}
    
    def create_task(self, task_type: str, metadata: Optional[Dict] = None) -> str:
        """
        创建新任务
        
        Args:
            task_type: 任务类型
            metadata: 额外元数据
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        now = datetime.now()
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {}
        )
        
        with self._task_lock:
            self._tasks[task_id] = task
        
        self._persist()
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务——若文件已被其他进程更新则自动重载"""
        if self._needs_reload():
            self._load_from_disk()
        with self._task_lock:
            return self._tasks.get(task_id)
    
    def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[int] = None,
        message: Optional[str] = None,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
        progress_detail: Optional[Dict] = None
    ):
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 新状态
            progress: 进度
            message: 消息
            result: 结果
            error: 错误信息
            progress_detail: 详细进度信息
        """
        with self._task_lock:
            task = self._tasks.get(task_id)
            if task:
                task.updated_at = datetime.now()
                if status is not None:
                    task.status = status
                if progress is not None:
                    task.progress = progress
                if message is not None:
                    task.message = message
                if result is not None:
                    task.result = result
                if error is not None:
                    task.error = error
                if progress_detail is not None:
                    task.progress_detail = progress_detail
        
        self._persist()
    
    def complete_task(self, task_id: str, result: Dict):
        """标记任务完成"""
        self.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            progress=100,
            message=t('progress.taskComplete'),
            result=result
        )
    
    def fail_task(self, task_id: str, error: str):
        """标记任务失败"""
        self.update_task(
            task_id,
            status=TaskStatus.FAILED,
            message=t('progress.taskFailed'),
            error=error
        )
    
    def list_tasks(self, task_type: Optional[str] = None) -> list:
        """列出任务"""
        if self._needs_reload():
            self._load_from_disk()
        with self._task_lock:
            tasks = list(self._tasks.values())
            if task_type:
                tasks = [t for t in tasks if t.task_type == task_type]
            return [t.to_dict() for t in sorted(tasks, key=lambda x: x.created_at, reverse=True)]
    
    def find_task_by_metadata(self, key: str, value: str) -> Optional[Task]:
        """通过 metadata 字段查找任务"""
        if self._needs_reload():
            self._load_from_disk()
        with self._task_lock:
            for task in self._tasks.values():
                if task.metadata.get(key) == value:
                    return task
        return None
    
    def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        
        with self._task_lock:
            old_ids = [
                tid for tid, task in self._tasks.items()
                if task.created_at < cutoff and task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
            ]
            for tid in old_ids:
                del self._tasks[tid]
        
        if old_ids:
            self._persist()

