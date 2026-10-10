# 重构分支运行隔离

重构分支默认使用以下端口和运行目录：

    后端：http://127.0.0.1:8002
    前端：http://127.0.0.1:5174
    运行根目录：.runtime/refactor

因此不会使用基线版本的 `resources/tasks/registry.json`、`resources/tasks/runs/` 或 `data/spo2-runs/`。

可通过环境变量覆盖：

    SOTABAND_API_PORT
    SOTABAND_FRONTEND_PORT
    SOTABAND_RUNTIME_ROOT
    SOTABAND_TIMESERIES_RUNS_DIR
    SOTABAND_PROCESSED_DATA_DIR
    SOTABAND_TEMP_DIR
    SOTABAND_LOGS_DIR

启动重构分支：

    cd D:\code\SOTABand-refactor
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8002

另开终端启动前端：

    cd D:\code\SOTABand-refactor\frontend
    npm run dev -- --host 127.0.0.1 --port 5174

基线版本仍使用原来的 8001、5173 和历史运行目录。两个版本同时运行时，不要设置相同的 `SOTABAND_RUNTIME_ROOT`。
