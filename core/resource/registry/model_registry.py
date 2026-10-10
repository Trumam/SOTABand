"""模型注册中心"""

import json
import time
from pathlib import Path

from core.resource.registry.json_store import update_json_list
from core.resource.registry.registry_base import BaseRegistry
from core.runtime.paths import MODEL_DIR as RUNTIME_MODEL_DIR
from core.runtime.paths import model_groups_path, model_registry_path

MODEL_DIR = Path(__file__).resolve().parent.parent.parent.parent / "resources" / "models"
REGISTRY_FILE = model_registry_path()


class ModelRegistry(BaseRegistry):
    """模型注册中心"""

    def __init__(self):
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        RUNTIME_MODEL_DIR.mkdir(parents=True, exist_ok=True)
        (RUNTIME_MODEL_DIR / "definitions").mkdir(parents=True, exist_ok=True)
        (MODEL_DIR / "models").mkdir(parents=True, exist_ok=True)
        if not REGISTRY_FILE.exists():
            self._write([])

    def _read(self) -> list[dict]:
        with open(REGISTRY_FILE, encoding='utf-8') as f:
            return json.load(f)

    def _write(self, data: list[dict]):
        with open(REGISTRY_FILE, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_def_dir(self) -> Path:
        return RUNTIME_MODEL_DIR / "definitions"

    def _get_models_dir(self) -> Path:
        return MODEL_DIR / "models"

    @staticmethod
    def default_group_path(resource: dict) -> str:
        """Use explicit registration metadata; the core registry has no domain rules."""
        return str(resource.get("group_path") or resource.get("domain_group") or "其它模型")

    async def register(self, resource: dict | None = None, **kwargs) -> str:
        if resource is None:
            resource = kwargs
        model_id = resource.get("id", f"model-{int(time.time())}")
        name = resource.get("name", model_id)

        entry = {
            "id": model_id,
            "name": name,
            "version": resource.get("version", "0.1.0"),
            "type": "model",
            "status": "registered",
            "spec_path": str(self._get_def_dir() / f"{model_id}.md"),
            "framework": resource.get("framework", ""),
            "model_path": resource.get("model_path", f"models/{model_id}/"),
            "input_format": resource.get("input_format", ""),
            "output_format": resource.get("output_format", ""),
            "tags": resource.get("tags", []),
            "associated_tool_id": resource.get("associated_tool_id", ""),
            "dataset_id": resource.get("dataset_id", ""),
            "model_name": resource.get("model_name", ""),
            "model_type": resource.get("model_type", ""),
            "config_path": resource.get("config_path", ""),
            "scaler_path": resource.get("scaler_path", ""),
            "metrics_path": resource.get("metrics_path", ""),
            "threshold": resource.get("threshold"),
            "task_id": resource.get("task_id", ""),
            "runtime_status": resource.get("runtime_status", "configured"),
            "training_config": resource.get("training_config", {}),
            "config_schema": resource.get("config_schema", {}),
            "catalog_model_id": resource.get("catalog_model_id", ""),
            "creation_type": resource.get("creation_type", "catalog-model"),
            "derived_from_model_id": resource.get("derived_from_model_id", ""),
            "manifest_path": resource.get("manifest_path", ""),
            "group_path": resource.get("group_path") or self.default_group_path(resource),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        def upsert(data):
            existing = next((i for i, e in enumerate(data) if e["id"] == model_id), None)
            names = {e.get("name") for e in data if e.get("id") != model_id}
            unique_name = name
            suffix = 1
            while unique_name in names:
                unique_name = f"{name}_{suffix}"
                suffix += 1
            entry["name"] = unique_name
            if existing is None:
                data.append(entry)
            else:
                data[existing] = entry

        update_json_list(REGISTRY_FILE, upsert)

        # 保存 MD 规范文档
        if "raw_md" in resource:
            spec_path = self._get_def_dir() / f"{model_id}.md"
            spec_path.parent.mkdir(parents=True, exist_ok=True)
            spec_path.write_text(resource["raw_md"], encoding="utf-8")

        return model_id

    async def unregister(self, resource_id: str):
        def remove(data):
            data[:] = [entry for entry in data if entry["id"] != resource_id]

        update_json_list(REGISTRY_FILE, remove)
        spec_path = self._get_def_dir() / f"{resource_id}.md"
        if spec_path.is_file():
            spec_path.unlink()

    async def get(self, resource_id: str) -> dict | None:
        for e in self._read():
            if e["id"] == resource_id:
                return {**e, "group_path": e.get("group_path") or self.default_group_path(e)}
        return None

    async def list_all(self) -> list[dict]:
        return [
            {**entry, "group_path": entry.get("group_path") or self.default_group_path(entry)}
            for entry in self._read()
        ]

    def _read_groups(self) -> list[dict]:
        try:
            value = json.loads(model_groups_path().read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            value = []
        return value if isinstance(value, list) else []

    def _write_groups(self, groups: list[dict]) -> None:
        model_groups_path().write_text(
            json.dumps(groups, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    async def list_groups(self) -> list[dict]:
        groups = self._read_groups()
        known = {str(item.get("name")) for item in groups}
        for name in {self.default_group_path(entry) for entry in self._read()}:
            if name not in known:
                groups.append({"id": name, "name": name, "system": True})
        return groups

    async def create_group(self, name: str) -> dict:
        clean = " ".join(str(name or "").split()).strip()
        if not clean or len(clean) > 80:
            raise ValueError("分组名称不能为空且不能超过 80 个字符")
        groups = await self.list_groups()
        existing = next((item for item in groups if item.get("name") == clean), None)
        if existing:
            return existing
        group = {"id": f"custom-{int(time.time())}", "name": clean, "system": False}
        groups.append(group)
        self._write_groups(groups)
        return group

    async def update(self, resource_id: str, updates: dict):
        def change(data):
            for entry in data:
                if entry["id"] == resource_id:
                    entry.update(updates)

        update_json_list(REGISTRY_FILE, change)
